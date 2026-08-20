## 1. Spec

- [ ] 1.1 Add `adversarial-review` capability spec (roles, format, location)
- [ ] 1.2 Add `qa-testing` capability spec (test plans, report, bugs, release gate)
- [ ] 1.3 Update `planning-gate` (adversarial review, decompose-large, escape hatch)
- [ ] 1.4 Update `environments` (stage progression: dev → staging after QA approve)

## 2. Agent SOUL.md

- [ ] 2.1 tech-pm: product lens + decompose-large
- [ ] 2.2 developer: engineering lens
- [ ] 2.3 devops: infra lens + release pipeline (dev → staging)
- [ ] 2.4 qa: testability lens + test plans / report / bugs / release gate

## 3. Docs

- [ ] 3.1 Update FACTORY-STANDARD.md (full workflow + escape hatch)
- [ ] 3.2 Update README.md (full workflow)

## 4. Hygiene

- [ ] 4.1 .gitignore: whitelist hermes-home (SOUL/config/gitconfig), ignore scratch artifacts

## 5. Restart agents

- [ ] 5.1 Recreate the agent containers so the SOUL.md changes take effect
