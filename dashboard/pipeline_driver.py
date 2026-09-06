#!/usr/bin/env python3
"""Deterministic pipeline driver — advances review -> merge -> fix WITHOUT an LLM.

The review loop used to stall because an LLM cron had to *decide* on each tick
whether to dispatch a review, merge, or ping the developer — and it kept missing
the transition. This script replaces that decision loop with fixed rules over
the repo's open PRs:

    R1  open PR, no qa verdict AND no tech-pm verdict  -> dispatch reviews
    R2  open PR, both latest verdicts approve           -> merge (squash+delete)
    R3  open PR, any latest verdict needs-changes       -> dispatch "fix" to dev

The ONLY LLM judgment left is the review agents' verdict ("is this code good?").
"What to do next" is a pure function of those verdicts — no model, no discretion.

Idempotent via a JSON state file keyed by PR number, so a restart or a
re-entrant cron tick never double-dispatches or double-merges.

One pass per run (cron-friendly): it checks open PRs, applies at most the
actions each PR needs, prints what it did, then exits. Empty stdout == nothing
happened (silent cron tick). Stdlib only; runs on the host like the watcher.

Usage:
    python3 dashboard/pipeline_driver.py            # one pass, then exit
    DRIVER_DRY_RUN=1 python3 dashboard/pipeline_driver.py   # preview only
"""

import json
import os
import re
import subprocess

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

# Review agents identify themselves in the comment HEADER (first line), not the
# body — a PM comment that *mentions* "QA" (or vice versa) must not be
# misclassified.  QA -> "## QA Report …"; Tech PM -> "manager/spec-conformance
# review …" or "## Tech PM review …".
QA_MARKER = re.compile(r"\bqa\s+report\b", re.I)
PM_MARKER = re.compile(r"tech[- ]?pm|\bmanager\b|spec[- ]?conformance", re.I)
# Verdict wording varies across reviewers ("Verdict: approve", "ready to merge",
# "needs change"). Match the signals case-insensitively, without a hard
# "Verdict:" anchor — some reviewers phrase approval as "ready to merge".
APPROVE_RE = re.compile(r"\bapprov(?:e|ed|al)\b|lgtm|ship\s*it|ready\s*to\s*merge", re.I)
NEEDS_RE = re.compile(r"needs?[- ]?changes?|changes?\s+(?:requested|required)", re.I)
TICKET_RE = re.compile(r"\b([A-Z]{2,}-\d+)\b")

REVIEW_QA = "qa"
REVIEW_PM = "tech-pm"


# ---------------------------------------------------------------------------
# Pure logic (unit-testable, no I/O)
# ---------------------------------------------------------------------------

def _verdict(body):
    """Extract approve / needs-changes from a review comment body, or None."""
    if NEEDS_RE.search(body):
        return "needs-changes"
    if APPROVE_RE.search(body):
        return "approve"
    return None


def _reviewer(body):
    """Classify a review comment as qa / tech-pm from its title line only.

    The reviewer identifies themselves in the "## …" / "** …" title line; the
    body may mention the *other* reviewer (e.g. "per the manager finding") and
    must not flip the classification.
    """
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(">") or s.startswith("<"):
            continue
        if s.startswith("## ") or s.startswith("**"):
            if PM_MARKER.search(s):
                return REVIEW_PM
            if QA_MARKER.search(s):
                return REVIEW_QA
            break
    return None


def parse_verdicts(comments):
    """Latest verdict per reviewer, scanning comments in chronological order.

    Returns ``{"qa": None|"approve"|"needs-changes", "tech-pm": ...}``. A
    comment only counts as a review if it names the reviewer (in its header)
    and carries a verdict signal; later comments overwrite earlier ones.
    """
    out: dict[str, str | None] = {REVIEW_QA: None, REVIEW_PM: None}
    for body in comments:
        v = _verdict(body)
        if v is None:
            continue
        r = _reviewer(body)
        if r is not None:
            out[r] = v
    return out


def decide(number, title, head, comments, state):
    """Return the list of actions for one PR, respecting the state file.

    Actions: ("reviews", n, title) | ("fix", n, title) | ("re-review", n, title)
             | ("merge", n, title).  A small stage machine (review -> fix ->
    re-review -> merge) driven by the PR head SHA; a head change while the
    developer was fixing triggers a re-review instead of stalling.
    """
    st = state.get(str(number), {})
    if st.get("merged"):
        return []
    v = parse_verdicts(comments)
    stage = st.get("stage", "review")          # review | fix | re-review
    seen = st.get("head")
    head_changed = seen is not None and seen != head

    # R2: both reviewers approve -> merge.
    if v[REVIEW_QA] == "approve" and v[REVIEW_PM] == "approve":
        return [("merge", number, title)]

    # R3: any latest verdict is needs-changes.
    if v[REVIEW_QA] == "needs-changes" or v[REVIEW_PM] == "needs-changes":
        if stage == "fix" and head_changed:
            # developer pushed a fix -> ask reviewers to re-review.
            return [("re-review", number, title)]
        if stage == "review":
            # reviewers just flagged needs-changes -> ask the developer to fix.
            return [("fix", number, title)]
        return []  # fix dispatched (awaiting push) or re-review dispatched (awaiting re-review)

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
    return (
        f"Ticket {ticket}: review PR #{number} ({title}). "
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


def _re_review_brief(ticket, number, title):
    return (
        f"Ticket {ticket}: re-review PR #{number} ({title}) — the developer pushed "
        f"a fix. Re-check the previously blocking findings and post your verdict "
        f"(`Verdict: approve` or `Verdict: needs-changes`). "
        f"Prefix AI comments with: > *This was generated by AI.*"
    )


def apply(action, state, head):
    kind, number, title = action
    key = str(number)
    st = state.setdefault(key, {})
    ticket = _ticket(title) or "(no-ticket)"

    if kind == "reviews":
        dispatch(REVIEW_QA, _review_brief(ticket, number, title, "qa"))
        dispatch(REVIEW_PM, _review_brief(ticket, number, title, "tech-pm"))
        st["stage"] = "review"
        st["head"] = head
        print(f"[driver] dispatched reviews for PR #{number} ({title})")
    elif kind == "re-review":
        dispatch(REVIEW_QA, _re_review_brief(ticket, number, title))
        dispatch(REVIEW_PM, _re_review_brief(ticket, number, title))
        st["stage"] = "re-review"
        st["head"] = head
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
        print(f"[driver] dispatched fix for PR #{number} ({title})")


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
            apply(action, state, head)
            acted = True
    if acted:
        save_state(state)


if __name__ == "__main__":
    main()
