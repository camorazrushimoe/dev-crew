# Proposal: Foundation docs describe the current model

## Why

The foundation docs still present two retired mechanisms as live, which
misleads operators of new instances and spawned today's batch of stale
implementation attempts (#24–#26, #29–#31, #33, #34 — all canceled as stale
with the `stale` label).

1. **`completion_watcher` / launchd task hooks.** `README.md` and
   `docs/architecture.md` describe `dashboard/completion_watcher.py` as the
   deterministic task-hooks runtime — a separate process that tails each
   gateway log and turns inbound/response into `task.started` /
   `task.finished` / `task.stale` bus events plus Linear auto-comments and a
   manager webhook ping. Nothing starts it anymore. Task signals come from
   **gateway completion hooks** (agent:start / agent:end handlers →
   `office:events` on the shared bus); agents are containers under the Office
   lifecycle controller. `completion_watcher.py` survives in the tree only as
   an unstarted legacy artifact.

2. **Shared `/workspace` clone model.** The docs present `/workspace` as the
   shared code area where project work lives and agents work on feature
   branches (`workspace/<project>/ (its own git repo)`, the workspace access
   table, "a shared bind-mounted directory where code lives"). Current model:
   agents work in **private clones under their hermes-home**; GitHub is the
   shared medium; the shared `/workspace` is **team tooling/env** (per-project
   services/compose mounts), not the work clone.

This change aligns the docs with reality. Docs-only: no runtime code changes.

## What changes

- Drop, or explicitly flag as legacy, every `completion_watcher` / launchd
  reference in `README.md`, `docs/architecture.md` and `.env.example`. Where a
  task-hooks note is needed, point at the current deterministic signal path:
  gateway completion hooks → shared bus (`task-completion` spec).
- Align clone-model text in `README.md`, `docs/architecture.md` and
  `workspace/README.md` with the private-hermes-home-clone reality, and describe
  shared `/workspace` as the team tooling/env mount, not the work clone
  location.

## Acceptance criteria

- No passage in `README.md`, `docs/architecture.md` or `workspace/README.md`
  presents `completion_watcher`, log-tail task hooks or launchd as the current
  runtime — remaining references are dropped or carry an explicit legacy marker
  pointing at the gateway-hook signal path.
- No passage in those files presents shared `/workspace` as the project
  work-clone location or as where agents keep their working trees.
- `.env.example` no longer points at `dashboard/completion_watcher.py` as the
  consumer of its task-completion variables.
- The PR diff is docs and config-template comments only — no runtime code.

## Impact

- `README.md`, `docs/architecture.md`, `workspace/README.md`, `.env.example`
- `openspec/changes/foundation-docs-current-model/` — this change (proposal,
  tasks). No capability-spec delta: nothing about runtime behaviour changes.

## Out of scope

- Runtime code (nothing runs differently after this change).
- Deleting `dashboard/completion_watcher.py` from the tree (a separate cleanup,
  if wanted).
- Capability-spec reconciliation: `agent-roles`, `layer-separation` and
  `task-completion` still encode parts of the older model; aligning the specs
  with the retired runtime is a separate follow-up change, not this docs pass.
- `docs/office-template.md` — audited: it contains no completion_watcher /
  launchd or clone-model claims (contract text only), so it needs no edit.
