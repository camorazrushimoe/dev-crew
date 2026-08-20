## Why

The factory only reviews a spec indirectly (plan review by dev+qa), devops joins
only at deploy, and QA has no explicit place in the release pipeline (test plans,
reports, bug publication, release gate). The full workflow was never written down
as a shared contract. This change formalises the end-to-end workflow: adversarial
spec review up front, a QA testing stage, a dev→staging pipeline gated on QA
approval, and an escape hatch that records shortcuts as tech debt.

## What Changes

- Add an adversarial spec-review stage before planning, by all four agents.
- Give each agent a role lens (product / engineering / infra / testability).
- Constrain reviews: verdict + at most 3 blocking findings; non-blocking goes to
  the backlog; no redesign proposals.
- Post reviews as comments on the spec's GitHub issue (one per agent), not Linear.
- Document the full end-to-end workflow in README + FACTORY-STANDARD.
- Add a QA testing stage (test plans, test report, bugs to the bus, release gate).
- Add a dev→staging deployment pipeline gated on QA approval.
- Add an escape hatch: the manager may override the workflow, recorded as tech debt.
- Ignore agent scratch artifacts in hermes-home (whitelist SOUL/config/gitconfig).

## Capabilities

### New Capabilities

- `adversarial-review`: the spec-review gate (roles, format, location).
- `qa-testing`: test plans, test report, bugs to the bus, release gate.

### Modified Capabilities

- `planning-gate`: insert the adversarial-review stage, decompose-large, escape hatch.
- `environments`: stage progression (dev → staging after QA approval).

## Impact

- `openspec/specs/adversarial-review/spec.md` — new.
- `openspec/specs/qa-testing/spec.md` — new.
- `openspec/specs/planning-gate/spec.md` — updated workflow + escape hatch.
- `openspec/specs/environments/spec.md` — stage progression.
- `agents/<role>/hermes-home/SOUL.md` — review lens + QA/release duties.
- `crew/FACTORY-STANDARD.md` — full workflow.
- `README.md` — full workflow.
- `.gitignore` — ignore agent scratch artifacts.
