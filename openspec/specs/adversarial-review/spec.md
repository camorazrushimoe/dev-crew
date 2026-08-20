# Adversarial Review

## ADDED Requirements

### Requirement: Review before planning

Every new spec or change SHALL pass an adversarial review by every agent that
will be involved in the work, BEFORE any plan or implementation.

#### Scenario: a new spec triggers review

- **WHEN** a new spec or change arrives in the factory
- **THEN** every involved agent SHALL review it adversarially
- **AND** no plan or code SHALL be produced before the reviews are posted

### Requirement: Role lenses

Each agent SHALL review from its own lens only:

| Agent | Lens | Focus |
|---|---|---|
| `tech-pm` | Product | value and priority, completeness, usability; can the idea be better / more convenient (an evaluation, not a redesign) |
| `developer` | Engineering | can the same result be achieved simpler, more efficiently, or cheaper in resources; ambiguous or underspecified parts |
| `devops` | Infrastructure | new services/dependencies, what is not yet deployed, what could break at deploy time |
| `qa` | Testability | how to test it, whether the Gherkin (Given/When/Then) is adequate, which scenarios cannot be tested at all |

#### Scenario: an agent stays in its lens

- **WHEN** an agent reviews a spec
- **THEN** it SHALL evaluate from its own lens
- **AND** SHALL NOT step outside its role

### Requirement: Evaluation, not redesign

Agents SHALL flag risks, gaps and ambiguities, but SHALL NOT propose an
alternative implementation or a redesign.

#### Scenario: flags, not redesigns

- **WHEN** an agent reviews a spec
- **THEN** it SHALL flag risks, gaps and ambiguities
- **AND** SHALL NOT propose a different implementation

### Requirement: Bounded review format

Each agent SHALL post its review with a verdict and a bounded set of findings.

#### Scenario: verdict and bounded findings

- **WHEN** an agent posts a review
- **THEN** it SHALL state a verdict (`approve` or `needs-changes`)
- **AND** SHALL list at most 3 blocking findings
- **AND** MAY list non-blocking findings (which go to the backlog and do not block)

### Requirement: Review location

Reviews SHALL be posted as comments on the spec's GitHub issue, one comment per
agent. No Linear ticket is required for the review itself.

#### Scenario: review in GitHub

- **WHEN** an agent completes its review
- **THEN** it SHALL post it as a comment on the spec's GitHub issue
- **AND** SHALL NOT require a Linear ticket for the review

### Requirement: DevOps participation

DevOps SHALL review every spec, and SHALL reply "N/A — no infrastructure impact"
when the spec has no new service, dependency, or environment change.

#### Scenario: no infra impact

- **WHEN** a spec introduces no new service, dependency, or environment change
- **THEN** devops SHALL reply "N/A — no infrastructure impact"
