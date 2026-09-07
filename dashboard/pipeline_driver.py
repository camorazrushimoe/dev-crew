#!/usr/bin/env python3
"""Deterministic pipeline driver — advances review -> merge -> fix WITHOUT an LLM.

The review loop used to stall because an LLM cron had to *decide* on each tick
whether to dispatch a review, merge, or ping the developer — and it kept missing
the transition. This script replaces that decision loop with fixed rules over
the repo's open PRs:

    R1  open PR, no qa verdict AND no tech-pm verdict    -> dispatch reviews
    R2  open PR, both latest verdicts approve            -> merge (squash+delete)
    R3  open PR, any latest verdict needs-changes        -> dispatch "fix" to dev
    R4  completed fix rounds reached DRIVER_MAX_REVIEW_ROUNDS (default 2) and the
        latest verdict is needs-changes again            -> needs-human (loop breaker)
    R5  a needs-human PR is terminal: no fix / re-review / merge dispatch until a
        human resets the state entry (needs_human: false / clears it)

R4/R5 are the review-cycle loop breaker (#35): a developer<->reviewer loop on
one PR cannot run past the cap without a human. A round is one completed
needs-changes cycle (a fix dispatch); both reviewers posting needs-changes on
the same head count as one round. Cap escalation is durable where humans read:
a needs-human PR comment and, for ticket-bound PRs, a tech-pm dispatch that
moves the Linear ticket to needs-human/Blocked.

The ONLY LLM judgment left is the review agents' verdict ("is this code good?").
"What to do next" is a pure function of those verdicts — no model, no discretion.

Idempotent via a JSON state file keyed by PR number, so a restart or a
re-entrant cron tick never double-dispatches or double-merges. State entries
gain `rounds`, `needs_human`, `needs_human_at`, `reason`, and per-reviewer
verdict-comment counters (`qa_verdicts` / `pm_verdicts`) that distinguish a
*new* needs-changes after a re-review from the stale verdict that triggered it;
entries written by earlier versions behave as rounds 0 / needs_human false.

One pass per run (cron-friendly): it checks open PRs, applies at most the
actions each PR needs, prints what it did, then exits. Empty stdout == nothing
happened (silent cron tick). Stdlib only; runs on the host like the watcher.

Usage:
    python3 dashboard/pipeline_driver.py            # one pass, then exit
    DRIVER_DRY_RUN=1 python3 dashboard/pipeline_driver.py   # preview only
    DRIVER_MAX_REVIEW_ROUNDS=1 python3 dashboard/pipeline_driver.py
        # escalate to needs-human after one completed needs-changes fix round
        # (default 2, minimum 1)
"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone

REPO = os.environ.get("DRIVER_REPO", "camorazrushimoe/lichina")
STATE_FILE = os.environ.get(
    "DRIVER_STATE_FILE",
    os.path.expanduser("~/.hermes/cron/output/pipeline-driver-state.json"),
)
DRY_RUN = os.environ.get("DRIVER_DRY_RUN", "0") not in ("0", "", "false", "False")

# Only drive PRs whose title carries a ticket id (dev-crew work is ticket-bound;
# the owner's own spec/docs PRs carry no ticket and are managed by hand). Set
# DRIVER_REQUIRE_TICKET=0 to drive every open PR regardless.
REQUIRE_TICKET = os.environ.get("DRIVER_REQUIRE_TICKET", "1") not in ("0", "", "false", "False")

# Review-cycle loop breaker (#35): completed needs-changes fix rounds allowed per
# PR before the driver stops and marks it needs-human (R4/R5). Minimum 1.
def _max_review_rounds():
    raw = os.environ.get("DRIVER_MAX_REVIEW_ROUNDS", "2")
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


DRIVER_MAX_REVIEW_ROUNDS = _max_review_rounds()

# The driver's own PR comments (needs-human escalation) carry this HTML-comment
# sentinel on the first line so the verdict parser never reads them as reviews.
DRIVER_SENTINEL = "<!-- conveyor"

# Review agents sign their comment with a header line. QA always names itself
# ("## QA Report" / "## QA Review"); Tech PM uses "## Tech PM Review" or the
# older "manager/spec-conformance review" / "round-N re-review" phrasing. Match
# on the title line only, QA first, so a PM comment that *mentions* "QA" in its
# body (or a QA comment that mentions "manager") does not flip classification.
QA_MARKER = re.compile(r"\bqa\b", re.I)
PM_MARKER = re.compile(r"tech[- ]?pm|\bmanager\b|spec[- ]?conformance|\breview\b", re.I)
# Verdict wording varies across reviewers ("Verdict: approve", "ready to merge",
# "needs change"). The authoritative verdict sits on a "Verdict: …" line; a
# reviewer may *mention* a previous round's verdict ("round-3 was needs-changes")
# in the body, which must not flip the actual verdict. So anchor to "Verdict:"
# first, then fall back to loose phrasing.
APPROVE_RE = re.compile(r"\bapprov(?:e|ed|al)\b|lgtm|ship\s*it|ready\s*to\s*merge", re.I)
NEEDS_RE = re.compile(r"needs?[- ]?changes?|changes?\s+(?:requested|required)", re.I)
VERDICT_RE = re.compile(r"verdict\s*:\s*(approv\w*|needs?\s*-?\s*changes?)", re.I)
TICKET_RE = re.compile(r"\b([A-Z]{2,}-\d+)\b")

REVIEW_QA = "qa"
REVIEW_PM = "tech-pm"


# ---------------------------------------------------------------------------
# Pure logic (unit-testable, no I/O)
# ---------------------------------------------------------------------------

def _is_driver_comment(body):
    """True when the comment is the driver's own (machine sentinel leads it).

    The needs-human comment carries the sentinel on its FIRST line (design
    D4 / tasks.md); a review comment that merely *quotes* the sentinel later
    in its body is not a driver comment and must still parse as a review.
    """
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        return s.startswith(DRIVER_SENTINEL)
    return False


def _verdict(body):
    """Extract approve / needs-changes from a review comment body, or None.

    Anchor to the "Verdict: …" line first: a reviewer's body may reference a
    previous round's verdict ("QA's round-3 verdict was needs-changes") without
    changing the actual verdict on the current head. The driver's own comments
    carry the ``<!-- conveyor`` sentinel and are never verdicts.
    """
    if _is_driver_comment(body):
        return None
    m = VERDICT_RE.search(body)
    if m:
        w = m.group(1).lower()
        return "needs-changes" if ("need" in w or "chang" in w) else "approve"
    if NEEDS_RE.search(body):
        return "needs-changes"
    if APPROVE_RE.search(body):
        return "approve"
    return None


def _reviewer(body):
    """Classify a review comment as qa / tech-pm from its title line only.

    The reviewer identifies themselves in the "## …" / "** …" title line; the
    body may mention the *other* reviewer (e.g. "per the manager finding") and
    must not flip the classification. QA is matched first because it is the
    only reviewer whose title names "QA"; everything else that reads as a
    review (manager / spec-conformance / tech-pm / plain "review") is PM. The
    driver's own comments (``<!-- conveyor`` sentinel) are never reviews.
    """
    if _is_driver_comment(body):
        return None
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(">") or s.startswith("<"):
            continue
        if s.startswith("## ") or s.startswith("**"):
            if QA_MARKER.search(s):
                return REVIEW_QA
            if PM_MARKER.search(s):
                return REVIEW_PM
            break
    return None


def _verdict_pairs(comments):
    """Yield (reviewer, verdict) for each review comment, in chronological order.

    Shared scan behind the last-wins verdict map (parse_verdicts) and the
    per-reviewer counters (_verdict_counts): skip the driver's own comments
    (first-line sentinel) and any comment that is not a signed verdict, so the
    skip/parse/classify shape lives in exactly one place.
    """
    for body in comments:
        if _is_driver_comment(body):
            continue
        v = _verdict(body)
        if v is None:
            continue
        r = _reviewer(body)
        if r is not None:
            yield r, v


def parse_verdicts(comments):
    """Latest verdict per reviewer, scanning comments in chronological order.

    Returns ``{"qa": None|"approve"|"needs-changes", "tech-pm": ...}``. A
    comment only counts as a review if it names the reviewer (in its header)
    and carries a verdict signal; later comments overwrite earlier ones. The
    driver's own comments (``<!-- conveyor`` sentinel on the first line) are
    skipped.
    """
    out: dict[str, str | None] = {REVIEW_QA: None, REVIEW_PM: None}
    for r, v in _verdict_pairs(comments):
        out[r] = v
    return out


def _verdict_counts(comments):
    """Per-reviewer count of verdict comments (used for re-review freshness).

    A needs-changes verdict while a re-review is in flight may be the *stale*
    verdict that triggered the re-review or a *new* verdict on the re-reviewed
    head. The driver records these counts in state at each review/re-review
    dispatch; a larger count today means reviewers replied.
    """
    out = {REVIEW_QA: 0, REVIEW_PM: 0}
    for r, _ in _verdict_pairs(comments):
        out[r] += 1
    return out


def decide(number, title, head, comments, state):
    """Return the list of actions for one PR, respecting the state file.

    Actions: ("reviews", n, title) | ("fix", n, title) | ("re-review", n, title)
             | ("merge", n, title) | ("needs-human", n, title).  A small stage
    machine (review -> fix -> re-review -> merge) driven by the PR head SHA; a
    head change while the developer was fixing triggers a re-review instead of
    stalling. The loop breaker (R4/R5): each fix dispatch increments `rounds`,
    and a needs-changes verdict at/after the cap escalates to needs-human.
    """
    st = state.get(str(number), {})
    if st.get("merged") or st.get("needs_human"):
        return []
    v = parse_verdicts(comments)
    counts = _verdict_counts(comments)
    stage = st.get("stage", "review")          # review | fix | re-review
    seen = st.get("head")
    head_changed = seen is not None and seen != head
    rounds = st.get("rounds", 0)               # backward compat: absent == 0

    # R2: both reviewers approve -> merge.
    if v[REVIEW_QA] == "approve" and v[REVIEW_PM] == "approve":
        return [("merge", number, title)]

    # R3/R4: any latest verdict is needs-changes.
    if v[REVIEW_QA] == "needs-changes" or v[REVIEW_PM] == "needs-changes":
        if stage == "fix" and head_changed:
            # developer pushed a fix -> ask reviewers to re-review.
            return [("re-review", number, title)]
        if stage == "re-review":
            # Distinguish a NEW needs-changes (reviewers replied to our
            # re-review) from the stale verdict that triggered it: a verdict
            # count above the one recorded at dispatch means they replied.
            # Entries written before the counters existed default to "already
            # accounted for", so a legacy re-review still waits (no re-fix).
            qa_new = (
                v[REVIEW_QA] == "needs-changes"
                and counts[REVIEW_QA] > st.get("qa_verdicts", counts[REVIEW_QA])
            )
            pm_new = (
                v[REVIEW_PM] == "needs-changes"
                and counts[REVIEW_PM] > st.get("pm_verdicts", counts[REVIEW_PM])
            )
            if qa_new or pm_new:
                if rounds >= DRIVER_MAX_REVIEW_ROUNDS:
                    return [("needs-human", number, title)]
                return [("fix", number, title)]
            return []  # re-review dispatched, reviewers have not replied yet
        if stage == "review":
            # reviewers just flagged needs-changes -> fix, unless the cap is
            # already spent (then escalate instead of looping).
            if rounds >= DRIVER_MAX_REVIEW_ROUNDS:
                return [("needs-human", number, title)]
            return [("fix", number, title)]
        return []  # fix dispatched (awaiting push)

    # R1: nothing reviewed yet -> dispatch the review pair (once).
    if v[REVIEW_QA] is None and v[REVIEW_PM] is None and seen is None:
        return [("reviews", number, title)]

    # Partial (one review in, waiting for the other) -> do nothing.
    return []


# ---------------------------------------------------------------------------
# I/O (thin, stdlib + gh CLI + crew-send.py)
# ---------------------------------------------------------------------------

def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=90)
    return p.returncode, p.stdout.strip()


def list_open_prs():
    code, out = gh("pr", "list", "--repo", REPO, "--state", "open",
                   "--json", "number,title,headRefOid")
    if code != 0:
        return []
    try:
        prs = [(p["number"], p["title"], p.get("headRefOid") or "")
               for p in json.loads(out)]
    except (ValueError, TypeError):
        return []
    if REQUIRE_TICKET:
        # Only dev-crew work: PRs whose title carries a ticket id (BON-12 …).
        prs = [(n, t, h) for (n, t, h) in prs if TICKET_RE.search(t)]
    return prs


def pr_comments(number):
    code, out = gh("pr", "view", str(number), "--repo", REPO, "--json", "comments")
    if code != 0:
        return []
    try:
        return [c.get("body", "") for c in json.loads(out).get("comments", [])]
    except (ValueError, TypeError):
        return []


def _ticket(title):
    m = TICKET_RE.search(title)
    return m.group(1).upper() if m else ""


def dispatch(agent, message):
    """Send a message to an agent's door via crew-send.py (subprocess)."""
    crew_send = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "crew", "crew-send.py")
    if DRY_RUN:
        print(f"[driver] DRY-RUN dispatch {agent}: {message[:80]!r}")
        return 0, ""
    p = subprocess.run(["python3", crew_send, agent, message],
                       capture_output=True, text=True, timeout=30)
    return p.returncode, p.stdout.strip()


def merge(number):
    if DRY_RUN:
        print(f"[driver] DRY-RUN merge PR #{number}")
        return 0, ""
    return gh("pr", "merge", str(number), "--repo", REPO,
              "--squash", "--delete-branch")


def _review_brief(ticket, number, title, role):
    header = "## QA Review" if role == "qa" else "## Tech PM Review"
    return (
        f"Ticket {ticket}: review PR #{number} ({title}). "
        f"Start your comment with the header line `{header}`. "
        f"Post your verdict as a PR comment ending with exactly one of "
        f"`Verdict: approve` or `Verdict: needs-changes` "
        f"(needs-changes: <=3 blocking findings, each file + minimal fix). "
        f"Do not change code. Prefix AI comments with: > *This was generated by AI.*"
    )


def _fix_brief(ticket, number, title):
    return (
        f"Ticket {ticket}: PR #{number} ({title}) got `needs-changes`. "
        f"Read the review comments, fix the blocking findings, push to the same "
        f"branch, then post a comment `fixes pushed` so reviewers re-check. "
        f"Prefix AI comments with: > *This was generated by AI.*"
    )


def _re_review_brief(ticket, number, title, role):
    header = "## QA Review" if role == "qa" else "## Tech PM Review"
    return (
        f"Ticket {ticket}: re-review PR #{number} ({title}) — the developer pushed "
        f"a fix. Start your comment with the header line `{header}`. "
        f"Re-check the previously blocking findings and post your verdict "
        f"(`Verdict: approve` or `Verdict: needs-changes`). "
        f"Prefix AI comments with: > *This was generated by AI.*"
    )


def needs_human_comment(number, title, rounds):
    """Body of the needs-human PR comment (parser-neutral by construction).

    The first line is the machine sentinel; the header carries no reviewer
    token; the prose avoids verdict lexemes, so the driver can never re-read
    its own escalation as a review (design D4). The ticket is stated
    explicitly (spec: the comment SHALL state the ticket); an unticketed PR
    (DRIVER_REQUIRE_TICKET=0 mode) gets no ticket claim.
    """
    ticket = _ticket(title)
    label = f"Ticket {ticket} — PR #{number}" if ticket else f"PR #{number}"
    return (
        "<!-- conveyor:needs-human -->\n"
        "## Loop breaker\n"
        f"{label} ({title}) reached the review-cycle cap after {rounds} "
        "completed fix round(s). A human must intervene; the driver will "
        "dispatch no further fixes, re-reviews, or merges until the state "
        "entry is reset."
    )


def _needs_human_brief(ticket, number, title, rounds):
    return (
        f"Ticket {ticket}: PR #{number} ({title}) exhausted its review budget "
        f"({rounds} fix round(s) at DRIVER_MAX_REVIEW_ROUNDS="
        f"{DRIVER_MAX_REVIEW_ROUNDS}). Move the Linear ticket to the "
        f"needs-human/Blocked state and post a comment starting "
        f"`Needs human:` explaining the loop. Do not dispatch further work "
        f"on this ticket."
    )


def post_comment(number, body):
    """Post a PR comment via the gh CLI (best-effort; DRY_RUN previews)."""
    if DRY_RUN:
        print(f"[driver] DRY-RUN needs-human comment on PR #{number}")
        return 0, ""
    return gh("pr", "comment", str(number), "--repo", REPO, "--body", body)


def apply(action, state, head, comments):
    kind, number, title = action
    key = str(number)
    st = state.setdefault(key, {})
    ticket = _ticket(title) or "(no-ticket)"

    if kind == "reviews":
        counts = _verdict_counts(comments)
        dispatch(REVIEW_QA, _review_brief(ticket, number, title, "qa"))
        dispatch(REVIEW_PM, _review_brief(ticket, number, title, "tech-pm"))
        st["stage"] = "review"
        st["head"] = head
        st["qa_verdicts"] = counts[REVIEW_QA]
        st["pm_verdicts"] = counts[REVIEW_PM]
        print(f"[driver] dispatched reviews for PR #{number} ({title})")
    elif kind == "re-review":
        counts = _verdict_counts(comments)
        dispatch(REVIEW_QA, _re_review_brief(ticket, number, title, "qa"))
        dispatch(REVIEW_PM, _re_review_brief(ticket, number, title, "tech-pm"))
        st["stage"] = "re-review"
        st["head"] = head
        st["qa_verdicts"] = counts[REVIEW_QA]
        st["pm_verdicts"] = counts[REVIEW_PM]
        print(f"[driver] dispatched re-review for PR #{number} ({title})")
    elif kind == "merge":
        code, out = merge(number)
        if code == 0:
            st["merged"] = True
            print(f"[driver] merged PR #{number} ({title})")
        else:
            print(f"[driver] merge PR #{number} failed: {out}")
    elif kind == "fix":
        dispatch("developer", _fix_brief(ticket, number, title))
        st["stage"] = "fix"
        st["head"] = head
        st["rounds"] = st.get("rounds", 0) + 1  # one completed round per fix dispatch
        print(f"[driver] dispatched fix for PR #{number} ({title}) "
              f"(round {st['rounds']})")
    elif kind == "needs-human":
        rounds = st.get("rounds", 0)
        # Terminal state FIRST: whatever happens to the best-effort side
        # effects below, the PR must end this tick marked needs-human. A
        # non-terminal entry would make the next tick re-decide needs-human
        # and re-post a duplicate escalation comment (idempotency, spec).
        st["needs_human"] = True
        st["needs_human_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        st["reason"] = (
            f"review-cycle cap reached: {rounds} fix round(s) completed "
            f"(DRIVER_MAX_REVIEW_ROUNDS={DRIVER_MAX_REVIEW_ROUNDS})"
        )
        body = needs_human_comment(number, title, rounds)
        try:
            code, out = post_comment(number, body)
            if code != 0:
                print(f"[driver] needs-human comment PR #{number} failed: {out}")
        except Exception as exc:  # best-effort (D7): never crash the run
            print(f"[driver] needs-human comment PR #{number} error: {exc}")
        if ticket != "(no-ticket)":
            try:
                code, out = dispatch("tech-pm",
                                     _needs_human_brief(ticket, number, title, rounds))
                if code != 0:
                    print(f"[driver] tech-pm dispatch PR #{number} failed: {out}")
            except Exception as exc:  # best-effort (spec L59-60/L84-86)
                print(f"[driver] tech-pm dispatch PR #{number} error: {exc}")
        print(f"[driver] PR #{number} ({title}) marked needs-human "
              f"after {rounds} round(s)")


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    if DRY_RUN:
        return
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def main():
    state = load_state()
    acted = False
    for number, title, head in list_open_prs():
        comments = pr_comments(number)
        for action in decide(number, title, head, comments, state):
            apply(action, state, head, comments)
            acted = True
    if acted:
        save_state(state)


if __name__ == "__main__":
    main()
