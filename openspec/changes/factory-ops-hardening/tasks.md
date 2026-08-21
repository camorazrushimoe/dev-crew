## 1. Specs

- [ ] 1.1 Add `task-completion` capability (START/FINISH hooks, Linear auto-comment, manager push, stale)
- [ ] 1.2 Add `workspace-hygiene` capability (scratch location, pre-PR cleanup)
- [ ] 1.3 Add `skill-guardrails` capability (no unsupervised factory-skill edits, bus events)
- [ ] 1.4 Update `planning-gate` — Linear Projects as grouping unit
- [ ] 1.5 Update `observability` — run-supervision view (tickets + agents + cost)
- [ ] 1.6 Update `message-bus` — new actions (`task.started`, `task.finished`, `task.stale`, `skill.created`, `skill.patched`)

## 2. Factory standard + skills

- [ ] 2.1 Update `crew/FACTORY-STANDARD.md` (hygiene, skills, projects, completion)
- [ ] 2.2 Update `agents/tech-pm/skills/linear-workflow/SKILL.md` (projectCreate + linking issues)
- [ ] 2.3 Note in SOUL.md files: scratch location + no self-mod of factory skills (implementation follow-up)

## 3. Docs

- [ ] 3.1 Brief note in README.md under Dashboard / Workflow if needed

## 4. Implementation (out of scope for this PR — after review)

- [ ] 4.1 Hermes completion hook / door wrapper
- [ ] 4.2 Dashboard run-supervision page
- [ ] 4.3 Runtime skill-write guard + bus emission
- [ ] 4.4 SOUL.md / skill text updates + agent restart
