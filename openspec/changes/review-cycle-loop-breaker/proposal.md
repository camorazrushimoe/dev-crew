# Proposal: Review-cycle loop breaker (runaway-iteration guard)

## Why

Issue #35 (high-priority) states the factory has no guard against **runaway
iteration** — a ticket whose reviews keep returning `needs-changes` loops
`fix → re-review → needs-changes → fix → …` unbounded, converging on nothing
while burning tokens, with **no breaker and no human escalation**.

The guards named in the original issue text no longer exist:

- the LLM cron decision loop was replaced by the deterministic conveyor
  (`dashboard/pipeline_driver.py`, rules R1–R3 — PRs #41–#47);
- the completion-watcher runtime (`task.stale`, log-tail hooks) is retired and
  not started anywhere in the current architecture;
- the new office runtime has no `task.stale` equivalent (gateway hooks publish
  neutral `task.started` / `task.finished` envelopes; nothing tails logs).

So a silent **or** looping agent surfaces nowhere. This change adds the breaker
to the component that actually advances the loop: the conveyor.

## What

Extend the conveyor rules with a **review-cycle cap** and a terminal
**needs-human** state:

| completed `needs-changes` fix rounds | latest verdict is `needs-changes` again | driver action |
|---|---|---|
| `< cap` (default cap = 2) | yes | dispatch fix to the developer (unchanged R3) |
| `>= cap` | yes | **stop the auto-loop** — post a needs-human PR comment, mark the PR `needs-human` in state, dispatch a needs-human notice to tech-pm so the Linear ticket moves to a needs-human state with a comment. No further fix / re-review / merge dispatch until a human resets. |

The cap SHALL default to **2 completed `needs-changes` fix rounds** and SHALL
be configurable (`DRIVER_MAX_REVIEW_ROUNDS`, minimum 1).

## Where the signal comes from (current components)

Issue #35 is written against retired components; the spec re-derives the goal
from what exists today. The HOME of each guard:

| Signal | Current component | Home | In this change? |
|---|---|---|---|
| review-verdict rounds (`needs-changes` repeats) | conveyor (`dashboard/pipeline_driver.py`) | **dev-crew** | ✅ yes |
| bus silence (agent accepted a task, never finished; no log-tail) | office runtime (`office:events`, lifecycle controller) | **agent-office** (follow-up issue camorazrushimoe/agent-office#37) | ❌ out of scope |
| ticket state (`needs-human`) | Linear, via tech-pm (`linear-workflow`) | **dev-crew** (contract defined here; tech-pm executes on dispatch) | ✅ contract yes |
| human alert delivery (Telegram/webhook ping) | office runtime / cron | **agent-office** (issue #37) | ❌ out of scope |

The dev-crew conveyor makes the escalation **durable where humans read** (PR
comment + Linear ticket via tech-pm); it does NOT own the alert channel.

## Locked calls

- Machine-readable review verdicts stay the only input signal; no LLM in the
  decision path.
- Deterministic, idempotent, best-effort side effects (same as R1–R3).
- State file stays backward compatible: entries without the new keys are
  treated as `rounds: 0`, `needs_human: false`.
- A needs-human PR is terminal for the driver: no auto fix, no auto merge.
  Resumption requires an explicit human reset.
- The needs-human PR comment SHALL be written so the verdict parser ignores it
  (no reviewer header tokens, no verdict lexemes, leading `<!-- conveyor -->`
  sentinel) — otherwise the driver would mis-read its own comment.

## Out of scope

- Bus-silence / stale-agent detection and human alert delivery →
  agent-office#37 (follow-up filed with this batch).
- Per-ticket turn / api_calls / wall-clock budget surfacing → agent-office#37
  (the conveyor cannot see those numbers; it only sees review rounds).
- Retired-component cleanup in README/architecture docs → dev-crew Batch C.
- Linear state taxonomy beyond the existing blocked/needs-human contract
  (`openspec/specs/task-completion/spec.md`).
