## Why

The factory only reviews a spec indirectly: tech-pm writes a plan and developer+qa
review the plan. The spec itself — the idea — is never challenged before planning,
and devops is not involved until deploy. This lets bad ideas, unnecessary
complexity, and untestable requirements reach implementation.

## What Changes

- Add an adversarial spec-review stage before planning, by all four agents.
- Give each agent a role lens (product / engineering / infra / testability).
- Constrain reviews: verdict + at most 3 blocking findings; non-blocking goes to
  the backlog; no redesign proposals.
- Post reviews as comments on the spec's GitHub issue (one per agent), not Linear.
- Include devops (replies "N/A" when there is no infra impact).

## Capabilities

### New Capabilities

- `adversarial-review`: the spec-review gate (roles, format, location).

### Modified Capabilities

- `planning-gate`: insert the adversarial-review stage before planning.

## Impact

- `openspec/specs/adversarial-review/spec.md` — new.
- `openspec/specs/planning-gate/spec.md` — updated workflow.
- `agents/<role>/hermes-home/SOUL.md` — each agent gains its review lens + rules.
- `crew/FACTORY-STANDARD.md` — updated workflow.
