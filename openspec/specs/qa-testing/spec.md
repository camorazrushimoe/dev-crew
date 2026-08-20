# QA Testing

## ADDED Requirements

### Requirement: Test plans

QA SHALL maintain test plans for the project and SHALL update them when new code
is merged. Test plans SHALL live in the project repository.

#### Scenario: test plans are updated after a merge

- **WHEN** a change is merged
- **THEN** qa SHALL update the relevant test plan(s) in the project repo
- **AND** SHALL run them

### Requirement: Test report

QA SHALL record a test report for each release candidate: what passed, what
failed, severity, and a verdict (approved / rejected).

#### Scenario: a report is recorded

- **WHEN** qa finishes testing a build on `dev-env`
- **THEN** qa SHALL record a test report with a verdict

### Requirement: Bugs published to the bus

QA SHALL publish a `bug.found` action to the shared-memory bus for each bug, with
debugging info in the payload, and SHALL record the bug durably.

#### Scenario: a bug is published

- **WHEN** qa finds a bug
- **THEN** qa SHALL publish a `bug.found` action to the shared-memory bus
- **AND** SHALL include debugging info in the payload
- **AND** SHALL record the bug durably (issue/ticket)

### Requirement: Release gate

QA SHALL approve the build before it is promoted to staging. DevOps SHALL NOT
deploy to `staging-env` until QA approves.

#### Scenario: staging requires QA approval

- **WHEN** a build is ready for staging
- **THEN** qa SHALL approve it explicitly
- **AND** devops SHALL NOT deploy to `staging-env` without that approval
