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

# The review agents post verdicts as PR comments with these markers. This is
# the contract between the driver and the review agents (see the spec).
QA_MARKER = re.compile(r"\bqa\b", re.I)
PM_MARKER = re.compile(r"tech[- ]?pm", re.I)
# Capture the verdict word within ~60 chars after "verdict" (handles
# "Verdict: approve", "Verdict: `needs-changes`", "verdict: ✅ approve").
VERDICT_RE = re.compile(r"verdict[^\n]{0,60}(needs-?changes|approve)", re.I)
TICKET_RE = re.compile(r"\b([A-Z]{2,}-\d+)\b")

REVIEW_QA = "qa"
REVIEW_PM = "tech-pm"


# ---------------------------------------------------------------------------
# Pure logic (unit-testable, no I/O)
# ---------------------------------------------------------------------------

def parse_verdicts(comments):
    """Latest verdict per reviewer, scanning comments in chronological order.

    Returns ``{"qa": None|"approve"|"needs-changes", "tech-pm": ...}``. A
    comment only counts as a review if it names the reviewer and carries a
    verdict keyword; later comments overwrite earlier ones (re-reviews win).
    """
    out: dict[str, str | None] = {REVIEW_QA: None, REVIEW_PM: None}
    for body in comments:
        m = VERDICT_RE.search(body)
        if not m:
            continue
        verdict = "needs-changes" if "needs" in m.group(1).lower() else "approve"
        if PM_MARKER.search(body):
            out[REVIEW_PM] = verdict
        elif QA_MARKER.search(body):
            out[REVIEW_QA] = verdict
    return out


def decide(number, title, comments, state):
    """Return the list of actions for one PR, respecting the state file.

    Actions: ("reviews", n, title) | ("merge", n, title) | ("fix", n, title).
    """
    st = state.get(str(number), {})
    if st.get("merged"):
        return []
    v = parse_verdicts(comments)

    # R3: any latest verdict is needs-changes -> ping the developer to fix.
    if v[REVIEW_QA] == "needs-changes" or v[REVIEW_PM] == "needs-changes":
        if not st.get("fix_dispatched"):
            return [("fix", number, title)]
        return []

    # R2: both reviewers approve -> merge.
    if v[REVIEW_QA] == "approve" and v[REVIEW_PM] == "approve":
        return [("merge", number, title)]

    # R1: nothing reviewed yet -> dispatch the review pair (once).
    if v[REVIEW_QA] is None and v[REVIEW_PM] is None and not st.get("reviews_dispatched"):
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
                   "--json", "number,title")
    if code != 0:
        return []
    try:
        prs = [(p["number"], p["title"]) for p in json.loads(out)]
    except (ValueError, TypeError):
        return []
    if REQUIRE_TICKET:
        # Only dev-crew work: PRs whose title carries a ticket id (BON-12 …).
        prs = [(n, t) for (n, t) in prs if TICKET_RE.search(t)]
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


def apply(action, state):
    kind, number, title = action
    key = str(number)
    st = state.setdefault(key, {})
    ticket = _ticket(title) or "(no-ticket)"

    if kind == "reviews":
        dispatch(REVIEW_QA, _review_brief(ticket, number, title, "qa"))
        dispatch(REVIEW_PM, _review_brief(ticket, number, title, "tech-pm"))
        st["reviews_dispatched"] = True
        print(f"[driver] dispatched reviews for PR #{number} ({title})")
    elif kind == "merge":
        code, out = merge(number)
        if code == 0:
            st["merged"] = True
            print(f"[driver] merged PR #{number} ({title})")
        else:
            print(f"[driver] merge PR #{number} failed: {out}")
    elif kind == "fix":
        dispatch("developer", _fix_brief(ticket, number, title))
        st["fix_dispatched"] = True
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
    for number, title in list_open_prs():
        comments = pr_comments(number)
        for action in decide(number, title, comments, state):
            apply(action, state)
            acted = True
    if acted:
        save_state(state)


if __name__ == "__main__":
    main()
