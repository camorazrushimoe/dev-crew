## 1. Specs (this PR)

- [x] 1.1 Add `task-completion` capability (binding, state rules, best-effort, stale)
- [x] 1.2 Add `workspace-hygiene` capability (scratch definition, pre-PR cleanup)
- [x] 1.3 Add `skill-guardrails` capability (path layers, block factory writes)
- [x] 1.4 Update `planning-gate` — Linear Projects as grouping unit
- [x] 1.5 Update `observability` — run-supervision view + cost-missing
- [x] 1.6 Update `message-bus` + `bus/action-schema.json` (`devops` actor, new actions)

## 2. Factory standard + skills + SOUL (this PR)

- [x] 2.1 Update `crew/FACTORY-STANDARD.md`
- [x] 2.2 Update `agents/tech-pm/skills/linear-workflow/SKILL.md`
- [x] 2.3 Update `to-tickets` + `task-dispatch` for Projects / ticket binding
- [x] 2.4 SOUL.md: scratch location + no self-mod of factory skills (all four agents)

## 3. Docs

- [ ] 3.1 Brief note in README.md under Dashboard / Workflow (optional follow-up)

## 4. Implementation (after this PR merges)

- [ ] 4.1 Door-handler completion wrapper (preferred) or Hermes hook
- [ ] 4.2 Dashboard run-supervision page
- [ ] 4.3 Runtime skill-write guard + hermes-home bus emission
- [ ] 4.4 Recreate agent containers so SOUL.md changes take effect
