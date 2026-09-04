## Purpose

Deterministic advancement of the review → merge → fix loop, without an LLM
deciding the next action.

## ADDED Requirements

### Requirement: Verdict contract

Review agents SHALL post their verdict as a PR comment that names the reviewer
(`QA` / `Tech PM`) and carries exactly one of `Verdict: approve` or
`Verdict: needs-changes`.

#### Scenario: a review is machine-readable

- **WHEN** a review agent finishes a review
- **THEN** the PR comment SHALL contain the reviewer name and a verdict keyword
- **AND** the driver SHALL parse it without invoking an LLM

### Requirement: Deterministic next action

The driver SHALL map review verdicts to actions by fixed rules:

| state | action |
|---|---|
| no verdicts | dispatch review to qa + tech-pm |
| both `approve` | merge (squash + delete branch) |
| any `needs-changes` | dispatch "fix" to the developer |
| one verdict in | no action (wait) |

#### Scenario: approve → merge

- **WHEN** an open PR has an `approve` verdict from BOTH reviewers
- **THEN** the driver SHALL merge it

#### Scenario: needs-changes → fix

- **WHEN** an open PR has a `needs-changes` verdict from any reviewer
- **THEN** the driver SHALL dispatch a fix task to the developer exactly once

#### Scenario: fresh PR → review dispatch

- **WHEN** an open PR has no verdict from either reviewer
- **THEN** the driver SHALL dispatch a review task to qa and tech-pm exactly once

### Requirement: Idempotency

The driver SHALL record dispatched/merged state per PR so a re-run or restart
never double-dispatches or double-merges.

#### Scenario: re-entrant cron tick

- **WHEN** the driver runs again after already dispatching reviews for a PR
- **THEN** it SHALL NOT re-dispatch reviews for that PR

### Requirement: No LLM in the decision

The driver SHALL NOT invoke an LLM to choose the next action.

#### Scenario: decision is rule-based

- **WHEN** the driver processes a PR
- **THEN** the next action SHALL be computed from verdicts by fixed rules
- **AND** no model call SHALL be made to decide it

### Requirement: Best-effort side effects

Dispatch and merge SHALL be best-effort: a failure is logged and SHALL NOT
crash the driver or block other PRs.

#### Scenario: merge fails

- **WHEN** a merge fails (e.g. conflicts)
- **THEN** the driver SHALL log the failure
- **AND** SHALL continue processing other PRs
