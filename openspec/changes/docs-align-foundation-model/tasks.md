# Tasks: Align foundation docs with the current model

Docs-only implementation checklist (issue #48). Each item maps to an acceptance
criterion (AC1–AC4). Work file-by-file; no runtime code changes.

## 1. README.md

- [ ] Project layout: `dashboard/completion_watcher.py` line → mark
      **legacy/retired** ("deterministic task hooks are runtime/gateway-hook
      driven today — see task-completion spec") or drop the file from the layout
      table with a legacy note.
- [ ] Project layout: `workspace/` line → "shared tooling/env mount (gitignored);
      work clones live under each agent's hermes-home".
- [ ] Dashboard section: replace the "completion watcher is the deterministic
      task-hooks runtime" paragraph with the current model: gateway hooks →
      shared bus events (`task.started`/`task.finished`), dashboard/app.py +
      pipeline driver are live; completion_watcher is retired and not started.
- [ ] Any `.env` guidance tied to the watcher (`MANAGER_WEBHOOK_URL`,
      `WATCHER_STALE_MINUTES`) → flag as watcher-era/legacy or drop.

## 2. docs/architecture.md

- [ ] Components list: **completion watcher** bullet → legacy/retired marker +
      current signal path (gateway hooks → bus; Office lifecycle on live
      instances).
- [ ] Components list: **workspace** bullet → shared tooling/env mount, not
      "where code lives".
- [ ] Project-work table: `Project code | workspace/<project>/ (its own git
      repo)` → private clones under hermes-home are canonical; GitHub is the
      shared medium; `/workspace` is team tooling/env.
- [ ] Update-flow / layer sections: any "workspace holds project work" wording →
      align with the same model.

## 3. docs/office-template.md

- [ ] Check for completion_watcher / shared-workspace-clone wording; flag or
      align minimally (only if present — verify first).

## 4. workspace/README.md

- [ ] Header + agent-access table: reframe from "developer clones project repos,
      works on feature branches" to shared tooling/env area.
- [ ] "How projects live here" section: state that project code lives in private
      hermes-home clones pushed to GitHub; `/workspace` holds shared tooling,
      project env compose files, and team scratch/infra — not the work clone.

## 5. Acceptance sweep

- [ ] AC1: no paragraph presents completion_watcher/launchd as the live runtime.
- [ ] AC2: no paragraph presents shared `/workspace` as the work clone.
- [ ] AC3: `git diff` contains only docs (`.md`) — no `config.yaml*`, compose
      env/command, skills, or dashboard code changes.
- [ ] AC4: `workspace/README.md` matches the model.
- [ ] Comment on issue #48 with the merged PR + what changed.
