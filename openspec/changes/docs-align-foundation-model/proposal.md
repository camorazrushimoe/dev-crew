# Proposal: Align foundation docs with the current model

## Why

Issue #48: the template docs (README, architecture, office-template) still
present two **retired mechanisms** as the live model:

1. **completion_watcher / launchd task hooks** — README + architecture describe
   `dashboard/completion_watcher.py` as the deterministic task-hooks runtime
   (tail gateway logs, publish `task.started`/`task.finished`/`task.stale`,
   auto-comment Linear, ping the manager). That runtime is not started anywhere
   in the current architecture: task signals come from gateway hooks → shared
   bus, agents are containers under the Office lifecycle controller. The
   closures of #24-#26 and #33-#34 (canceled today as stale, `stale` label)
   derive from this retirement; Batch A's spec (#35, PR #49) already treats the
   watcher as retired.
2. **shared `/workspace` as the work clone** — README project layout,
   `docs/architecture.md`, and `workspace/README.md` describe `workspace/` as
   where agents clone project repos and work on feature branches. The actual
   model (closures of #29-#31, canceled today as stale) is: agents work in
   **private clones under their hermes-home**; GitHub is the shared medium;
   shared `/workspace` is **team tooling/env**, not the work clone.

Docs-only change: drop or explicitly flag as legacy the completion_watcher /
launchd references and align the clone-model wording with the current reality.
No runtime code changes.

## What

- **README.md** — project layout bullet for `dashboard/completion_watcher.py`
  and the Dashboard/observability paragraph: flag the watcher as **legacy /
  retired** (or drop), state that task signals come from gateway hooks → shared
  bus (Office lifecycle), and that the dashboard + pipeline driver are the
  live components. Align the `workspace/` bullet: shared tooling/env mount, not
  the work clone.
- **docs/architecture.md** — components list (completion watcher, workspace),
  project-work table (`Project code | workspace/<project>/`), and any
  watcher/workspace wording: flag watcher as legacy; state that project work
  happens in private hermes-home clones and that `/workspace` is team
  tooling/env.
- **docs/office-template.md** — if it references the watcher or the shared
  workspace clone model, flag/aligne the same way (checked during
  implementation; minimal edit).
- **workspace/README.md** — reframe: shared tooling/env area; project repos are
  not cloned/worked here by default (private hermes-home clones are canonical;
  GitHub is the shared medium).

## Acceptance criteria

- **AC1:** No README / docs / office-template paragraph presents
  `completion_watcher.py` (or launchd) as the live task-hooks runtime. Where it
  is still named, it is explicitly marked legacy/retired with the current
  signal path (gateway hooks → bus) stated.
- **AC2:** No foundation doc presents shared `/workspace` as the canonical work
  clone. Docs state: work clones live under each agent's hermes-home; GitHub is
  the shared medium; `/workspace` is team tooling/env.
- **AC3:** Docs-only — diff contains no runtime code changes (no `config.yaml*`,
  no compose command/env changes, no skills, no dashboard code).
- **AC4:** `workspace/README.md` agrees with the model above (no "developer
  clones project repos here" as the default work flow).

## Locked calls

- Minimal + factual edits: prefer a short "legacy/retired" marker + current-path
  pointer over deleting history wholesale where a component is still shipped in
  the repo (`dashboard/completion_watcher.py` exists but is not started).
- Keep this change separate from Batch B (config-render closeout) — no bundling.
- Spec record only: proposal + tasks with acceptance criteria (no capability
  spec delta needed — capability contracts (task-completion, workspace-hygiene)
  already describe the runtime/model-agnostic behavior).

## Out of scope

- Deleting `dashboard/completion_watcher.py` or other retired code (runtime
  change; separate cleanup if wanted).
- Changing capability specs (`task-completion`, `workspace-hygiene`) — they
  already describe the desired runtime/model-agnostic contract.
- Batch B's config-render/SSOT stale references — separate spec, separate PR.
