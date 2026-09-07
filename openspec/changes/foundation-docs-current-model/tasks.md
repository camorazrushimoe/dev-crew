# Tasks: foundation-docs-current-model (#48)

## 1. Spec (this PR)

- [x] 1.1 `proposal.md` — scope, acceptance criteria, out-of-scope boundary
- [x] 1.2 `tasks.md`

## 2. Docs implementation (follow-up PR, after this spec merges)

### completion_watcher / launchd

- [ ] 2.1 `README.md` — project layout: `dashboard/completion_watcher.py` entry
      dropped or marked legacy (not a current runtime component).
- [ ] 2.2 `README.md` — Dashboard section: remove the
      `python3 dashboard/completion_watcher.py` run step and rewrite the
      "completion watcher is the deterministic task-hooks runtime" paragraph to
      the current signal path (gateway completion hooks → shared bus,
      `task-completion` spec). If kept, the watcher text carries an explicit
      legacy marker.
- [ ] 2.3 `docs/architecture.md` — Components: completion-watcher bullet dropped
      or flagged legacy; task-signal bullet describes gateway hooks → shared
      bus instead of log-tail watching.
- [ ] 2.4 `.env.example` — task-completion comment block no longer names
      `dashboard/completion_watcher.py` as the consumer of
      `MANAGER_WEBHOOK_URL` / `WATCHER_STALE_MINUTES`.

### Clone model / shared workspace

- [ ] 2.5 `README.md` — project layout comment for `workspace/` and any
      "shared code area" wording: describe the team tooling/env mount (project
      services/compose), not the work clone location.
- [ ] 2.6 `docs/architecture.md` — Components "workspace" bullet and the
      project-work table row: work clones live in agents' private hermes-home
      (GitHub is the shared medium); `workspace/<project>` holds project
      services/tooling/env.
- [ ] 2.7 `workspace/README.md` — access table and conventions: agents do NOT
      clone project work or keep feature branches here; rewrite for the
      tooling/env reality.

### Verification

- [ ] 2.8 `grep -n completion_watcher README.md docs/architecture.md .env.example`
      → no unmarked live claim remains (legacy markers allowed).
- [ ] 2.9 Diff contains no runtime code changes (docs + config-template
      comments only).
