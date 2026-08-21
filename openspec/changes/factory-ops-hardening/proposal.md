## Why

The first real SpacedBro MVP run (2026-08-20) exposed five operational gaps in the
factory foundation:

1. **No push on task finish** (#12) — the manager had to poll Linear, GitHub PRs and
   container logs to know when an agent finished. Completion was prompt-level only.
2. **Epic tickets instead of Linear Projects** (#13) — skills teach "parent epic +
   children", but Linear Projects are the better grouping primitive (first-class
   filter, one view per product effort).
3. **Scratch files pollute the project workspace** (#14) — agents wrote review
   drafts into `workspace/<project>/`, dirtying `git status` and risking accidental
   commits.
4. **Unsupervised skill self-modification** (#15) — agents can create/patch skills
   at runtime (Hermes self-improvement). A drifted, gitignored `spec-review` skill
   already caused a Postgres-over-prescription bug (#9/#10).
5. **No single run-supervision view** (#16) — supervising a run required stitching
   Linear + GitHub + `docker exec` logs by hand. The existing dashboard only shows
   agent up/down/state, not tickets + cost + who is working on what.

## What Changes

- Add **deterministic task-completion hooks** (runtime, not prompt): START / FINISH
  signals that auto-comment Linear and ping the manager via webhook.
- Make **Linear Projects** the work-grouping unit (replace synthetic parent epics).
- Add a **workspace hygiene** rule: scratch only in `$HERMES_HOME` or `/tmp`, never
  in `workspace/`.
- Add **skill guardrails**: factory skills are not writable at runtime; runtime
  drafts under hermes-home are visible on the bus when feasible.
- Extend **observability** with a run-supervision view (tickets + agent activity +
  cost) grouped by Linear Project.

## Implementation priority (after this spec merges)

1. **Policy (cheap, immediate):** #13 Projects, #14 hygiene, #15 skill guardrails
   (docs + SOUL + RO mount already helps).
2. **Runtime signal:** #12 completion hooks (unblocks reliable supervision).
3. **Supervision UI:** #16 run view (builds on #12 + existing health dashboard).

## Capabilities

### New Capabilities

- `task-completion`: deterministic START/FINISH hooks, Linear auto-comment, manager
  push, stale-task signal, ticket binding, best-effort external side effects.
- `workspace-hygiene`: scratch location rules, pre-PR cleanup, no `git add -A`.
- `skill-guardrails`: block runtime writes to factory skills; path layers; bus
  visibility for hermes-home drafts.

### Modified Capabilities

- `planning-gate`: Linear Projects as the grouping unit (not parent epic tickets).
- `observability`: run-supervision view (tickets + agents + cost).
- `message-bus`: new actions (`task.started`, `task.finished`, `skill.created`,
  `skill.patched`, `task.stale`); `devops` actor in schema.

## Impact

- `openspec/specs/task-completion/spec.md` — new
- `openspec/specs/workspace-hygiene/spec.md` — new
- `openspec/specs/skill-guardrails/spec.md` — new
- `openspec/specs/planning-gate/spec.md` — Projects instead of epics
- `openspec/specs/observability/spec.md` — run-supervision view
- `openspec/specs/message-bus/spec.md` — new action types
- `bus/action-schema.json` — actor enum includes `devops`
- `crew/FACTORY-STANDARD.md` — hygiene + skills + projects + completion rules
- `agents/*/hermes-home/SOUL.md` — scratch + skill guardrails
- `agents/tech-pm/skills/linear-workflow/SKILL.md` — projectCreate + linking
- `agents/tech-pm/skills/to-tickets/SKILL.md` — Projects, not epics
- `agents/tech-pm/skills/task-dispatch/SKILL.md` — ticket id required in message
- Related issues: #12, #13, #14, #15, #16
