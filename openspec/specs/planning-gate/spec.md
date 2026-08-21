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

### Requirement: Adversarial review before planning

Before any plan or implementation, every involved agent SHALL adversarially
review the spec (see the `adversarial-review` capability).

#### Scenario: spec is reviewed before planning

- **WHEN** a new spec or change arrives
- **THEN** the involved agents SHALL post their adversarial reviews (GitHub issue)
- **AND** planning SHALL begin only after the reviews are posted

### Requirement: Plan before code

After the adversarial review, every task SHALL pass through a planning phase
before execution:

`task → adversarial review → tech-pm writes plan → developer + qa review →
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

### Requirement: Linear Projects are the grouping unit

A product effort SHALL be represented as a Linear **Project**, not as a synthetic
parent "epic" ticket. tech-pm SHALL create the Project and link every related
ticket to it. Tickets MAY still declare blocking edges between each other; the
Project is the filter and progress view.

#### Scenario: new product effort becomes a Project

- **WHEN** tech-pm decomposes a reviewed spec into implementation tickets
- **THEN** tech-pm SHALL create (or reuse) a Linear Project for the effort
- **AND** SHALL link every ticket in the effort to that Project
- **AND** SHALL NOT require an artificial parent epic ticket solely for grouping

#### Scenario: large work is still split

- **WHEN** a spec is too large for a single task
- **THEN** tech-pm SHALL split it into smaller tickets under the same Project
- **AND** SHALL dispatch them in a sensible order (blocking edges)

### Requirement: Escape hatch (critical override)

The manager MAY override the workflow in a critical situation by explicitly
approving the override. Every override SHALL be recorded immediately as tech debt.

#### Scenario: override is recorded as tech debt

- **WHEN** the manager overrides the workflow
- **THEN** the override SHALL be recorded as a tech-debt item (a GitHub issue
  labelled `tech-debt`, or a Linear ticket)
- **AND** the shortcut SHALL NOT be silent
