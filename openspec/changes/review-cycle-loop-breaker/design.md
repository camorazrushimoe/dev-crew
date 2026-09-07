# Design: Review-cycle loop breaker

Decision record for the Batch A spec (dev-crew #35). Supersedes the issue's
original solution text wherever it names retired components (completion
watcher, `task.stale`, the LLM cron "driver prompt"). Goal unchanged: **a
developer↔reviewer loop on one ticket must not run past the cap without a
human.**

## D1 — Home of each guard (what lives where)

Decided from current components, not from the retired architecture:

| Guard | Signal source (current) | Home | Rationale |
|---|---|---|---|
| Review-cycle cap (issue AC1) | conveyor verdict rounds | **dev-crew, this change** | The conveyor (`dashboard/pipeline_driver.py`) is the only component that advances `needs-changes → fix → re-review`; it already owns per-PR state. |
| Stale / silent agent (issue AC2) | `office:events` bus silence + lifecycle controller state | **agent-office#37** (follow-up filed this batch) | The template no longer runs a task-hooks runtime; in Office-attached mode task signals and container lifecycle are office-owned (`office/activity.py`, `docs/agent-lifecycle.md`). No log-tail exists or should be re-created in dev-crew. |
| Per-ticket budget (issue AC3, optional) | bus envelope telemetry (api_calls / duration / outcome) | **agent-office#37** | The conveyor sees GitHub PRs only — no turns, api_calls or wall-clock. Envelopes are currently neutral; enrichment is an office/activity.py + recorder change. |
| Human alert delivery | office cron / factory-control consumer | **agent-office#37** | Alerting the manager is the office control plane. Dev-crew side effects stay durable-and-human-readable (PR comment, Linear). |

Consequence for this change: the dev-crew spec implements **AC1** and defines
the **needs-human contract** (PR comment + Linear state + no-auto-continue)
that agent-office#37's alert consumer will watch.

## D2 — The budget: 2 completed needs-changes rounds (default)

`DRIVER_MAX_REVIEW_ROUNDS`, default **2**, minimum 1 (≥1). "Cannot run past 2
review cycles without human intervention" (issue AC1) reads as: two full
`needs-changes → fix → re-review` cycles may complete; a **third**
`needs-changes` verdict escalates instead of dispatching another fix.

## D3 — Counting semantics (rounds)

- A **round** is a completed `needs-changes` cycle: one fix dispatch to the
  developer, followed by the developer's push and a re-review verdict.
- `rounds` increments by 1 **when the driver dispatches a fix**; the counter is
  stored per PR in the state file.
- Both reviewers posting `needs-changes` on the same head still count as **one
  round** (R3 already emits a single fix dispatch regardless of how many
  reviewers said no).
- Cap check happens **before** a fix dispatch: if `rounds >= cap` and the
  latest verdict is `needs-changes`, the action is `needs-human`, never `fix`.

Worked trace with default cap = 2:

| step | event | state | driver action |
|---|---|---|---|
| 1 | PR open, no verdicts | stage review, rounds 0 | dispatch reviews (R1) |
| 2 | QA `needs-changes` | stage review, rounds 0 | dispatch fix (round 1) |
| 3 | dev pushes head H2 | stage fix, rounds 1 | dispatch re-review |
| 4 | QA `needs-changes` again | stage re-review, rounds 1 | rounds 1 < 2 → dispatch fix (round 2) |
| 5 | dev pushes head H3 | stage fix, rounds 2 | dispatch re-review |
| 6 | QA `needs-changes` again | stage re-review, rounds 2 | rounds 2 >= 2 → **needs-human** |

### Known current-machine gap the implementer MUST close (found during spec)

The stage machine has no transition for `stage == re-review` + a **new**
`needs-changes` verdict: `decide()` returns `[]`, so after one fix round a
second `needs-changes` re-review stalls silently instead of advancing (or
escalating). The loop breaker requires the driver to (a) advance round 2+ and
(b) escalate at the cap — so the implementer must add the missing transition
without double-dispatching while a re-review is still in flight.

Ambiguity to resolve deterministically: with `stage == re-review`, the latest
`needs-changes` comment may be the **old** verdict (reviewers have not replied
yet — the current `test_rereview_waiting_does_not_refix` case) or a **new**
verdict on the re-reviewed head. Comments carry no head SHA today, so the
recommended fix is a per-reviewer **verdict-comment counter** in state
(`qa_verdicts`, `pm_verdicts`): a verdict comment count greater than the count
recorded at re-review dispatch means "reviewers replied; advance the round".
The spec (delta) states the observable contract; this is the implementation
approach.

## D4 — needs-human behavior at the cap

When the cap is reached, the driver performs (all best-effort, no LLM):

1. **Post a needs-human PR comment** via `gh pr comment`:
   - first line is the sentinel `<!-- conveyor:needs-human -->`;
   - header `## Loop breaker` (no QA / tech-pm / manager / "review" header
     token — the parser classifies reviewers from header lines);
   - body prose with NO verdict lexemes (`approve`, `needs-changes`,
     `lgtm`, `ready to merge`, `changes requested`) so `_verdict()` cannot
     mis-read the driver's own comment;
   - states the ticket, the completed rounds, and that a human must intervene.
2. **Mark the state entry terminal**: `needs_human: true`, `needs_human_at`
   (UTC), `reason`, keeping `rounds`.
3. **Dispatch a needs-human task to tech-pm** (ticket-bound PRs only — the
   driver only auto-drives ticket-bound PRs when `DRIVER_REQUIRE_TICKET=1`,
   the default): message carries `Ticket <ID>`, the PR number, the rounds
   count, and the instruction to move the Linear ticket to the team's
   needs-human/Blocked state and post a comment starting `Needs human:` —
   and to **not** dispatch further work on the ticket.
4. **Record the escalation in the driver output/state** for the host log and
   for any bus consumer (agent-office#37 alert consumer watches the PR comment
   / Linear state; no new bus dependency is introduced by this change).

While `needs_human` is set, `decide()` returns no actions for that PR — even
if the developer pushes more commits or reviewers later post `approve`
(merging a PR that exhausted its review budget is a human decision).

## D5 — Human reset

Explicitly out-of-band (a human acting, not an agent):

- clear/reset the PR's state entry (`needs_human: false`, optionally reset
  `rounds`) in `DRIVER_STATE_FILE`, or
- merge/close the PR manually (`merged` is already terminal).

After a reset the driver MAY resume dispatching for that PR. No agent-facing
auto-reset exists.

## D6 — State file & config

Backward compatible per-PR entry additions:

```jsonc
{
  "42": {
    "stage": "re-review",
    "head": "abc123",
    "rounds": 2,              // new; absent == 0
    "needs_human": true,      // new; absent == false
    "needs_human_at": "2026-09-07T12:00:00Z",
    "reason": "3rd needs-changes verdict; DRIVER_MAX_REVIEW_ROUNDS=2"
  }
}
```

New env knobs:

| Env | Default | Meaning |
|---|---|---|
| `DRIVER_MAX_REVIEW_ROUNDS` | `2` | needs-changes fix rounds allowed before needs-human (>= 1) |

`DRIVER_DRY_RUN` previews the needs-human actions like any other action.

## D7 — Failure handling

Same contract as R1–R3: the needs-human comment, the tech-pm dispatch and
Linear side effects are best-effort; a failure is logged and SHALL NOT crash
the driver or block other PRs; state is saved once per run when anything
acted.

## D8 — Tests to add (implementation PR)

Pure-logic tests in `tests/test_pipeline_driver.py`:

1. third `needs-changes` after two fix rounds → `[("needs-human", …)]`
   (and no `fix`).
2. `DRIVER_MAX_REVIEW_ROUNDS=1` → second `needs-changes` escalates.
3. both reviewers `needs-changes` on the same head → one round (one fix).
4. needs-human terminal: `fix` / `re-review` / `merge` all suppressed while
   `needs_human: true`, even with new commits and `approve` verdicts.
5. human reset (state cleared) → driver resumes.
6. the needs-human PR comment body parses to no verdict / no reviewer
   (parser ignores the driver's own comment).
7. pre-existing state without `rounds` / `needs_human` behaves as 0 / false.
8. re-review returns `needs-changes` → advances round (fix or needs-human at
   cap) without double-dispatch (covers the D3 gap; reconciles
   `test_rereview_waiting_does_not_refix` with the verdict-comment counter).

## Non-goals / follow-ups

- Office-side stale/budget/alert work is tracked in
  **camorazrushimoe/agent-office#37** (filed with this batch); this design
  deliberately keeps dev-crew free of log-tail detection and alert channels.
- Legacy doc/spec text cleanup (README/architecture still describe the
  completion watcher) is dev-crew Batch C.
