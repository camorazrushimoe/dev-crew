# Proposal: Deterministic pipeline dispatch

Replace the LLM cron's review → merge → fix decision loop with a deterministic
driver that acts on review verdicts.

## Why

The review loop stalls. After a developer opens a PR, the completion watcher
marks it In Review but does **not** dispatch the next step. The next step —
dispatch reviews, merge on approve, ping the developer on needs-changes — was
left to an LLM cron deciding on a 5-minute tick, and it kept missing the
transition. Agents finished their review and nobody told the developer to fix
or the merger to merge.

## What

A deterministic driver (`dashboard/pipeline_driver.py`, stdlib-only, runs on
the host like the watcher) reads open PRs and applies fixed rules:

| state | action |
|---|---|
| no verdicts | dispatch review to qa + tech-pm |
| both `approve` | merge (squash + delete branch) |
| any `needs-changes` | dispatch "fix" to the developer |
| one verdict in | no action (wait) |

The only LLM judgment left is the review agents' verdict ("is this code
good?"). "What to do next" is a pure function of those verdicts.

## Locked calls

- Review agents keep posting `Verdict: approve` / `Verdict: needs-changes` in
  PR comments (already their convention).
- Idempotent via a JSON state file keyed by PR number: a restart or re-entrant
  cron tick never double-dispatches or double-merges.
- The LLM cron becomes a backup/observer, not the decision-maker.
- `DRIVER_DRY_RUN=1` previews actions without side effects.

## Out of scope

- Dispatching the *next* slice after a merge (still manager-driven).
- Re-review-after-fix automation (the fix message asks the developer to ping
  reviewers; a formal re-review dispatch is a follow-up).
- Detecting agent stalls — that remains the watcher's `task.stale` job.
