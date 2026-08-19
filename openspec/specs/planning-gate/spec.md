# Planning Gate

## ADDED Requirements

### Requirement: No spec, no work

When a task arrives without a reference to a spec (`openspec/changes/<change>/`
plus `openspec/specs/<capability>/`), agents SHALL stop and ask "Where is the
spec? Who wrote it?" before coding, testing, or planning.

#### Scenario: task without a spec is blocked

- **WHEN** a task arrives without a spec reference
- **THEN** the agent SHALL NOT start work
- **AND** SHALL ask the manager or tech-pm to point to the spec

### Requirement: Plan before code

Every task SHALL pass through a planning phase before execution:

`task → tech-pm writes plan (Linear comment) → developer + qa review →
manager approves → developer implements → qa verifies → merge → devops deploys`

#### Scenario: no approved plan blocks implementation

- **WHEN** a developer receives a task without an approved plan
- **THEN** the developer SHALL request a plan from tech-pm
- **AND** SHALL NOT improvise an implementation

#### Scenario: manager approval is the gate

- **WHEN** developer and qa have reviewed the plan in the ticket comments
- **THEN** implementation SHALL begin only after the manager explicitly approves ("go" / "approved")

### Requirement: Branch discipline

Implementation SHALL happen on a feature branch named `feature/<ticket>-<slug>`,
never on `main`/`master`. The developer SHALL open a PR and SHALL NOT merge its
own PR.

### Requirement: Review against the spec

QA (and the manager) SHALL review the PR against the spec's scenarios. Merging
SHALL happen only after review passes.
