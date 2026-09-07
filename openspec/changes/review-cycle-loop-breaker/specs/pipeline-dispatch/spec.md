## ADDED Requirements

### Requirement: Review-cycle cap (loop breaker)

The driver SHALL track completed `needs-changes` fix rounds per PR in its state
file (`rounds`). The driver SHALL stop auto-looping a PR once its completed
rounds reach the configured cap (`DRIVER_MAX_REVIEW_ROUNDS`, default 2,
minimum 1) and the latest review verdict is `needs-changes` again. Both
reviewers posting `needs-changes` on the same head SHALL count as one round.

#### Scenario: a loop cannot run past the cap

- **WHEN** a PR has completed 2 `needs-changes` fix rounds (default cap) and a
  reviewer posts `needs-changes` again
- **THEN** the driver SHALL NOT dispatch another fix
- **AND** SHALL mark the PR needs-human instead

#### Scenario: a needs-changes verdict advances the round

- **WHEN** a PR is in re-review, reviewers have replied, and the verdict is
  `needs-changes`
- **THEN** the driver SHALL advance the round: dispatch the next fix if rounds
  are below the cap, or mark the PR needs-human if the cap is reached
- **AND** SHALL NOT double-dispatch while a re-review is still in flight

#### Scenario: both reviewers on the same head count once

- **WHEN** both qa and tech-pm post `needs-changes` on the same head
- **THEN** the driver SHALL dispatch exactly one fix for that round

#### Scenario: the cap is configurable

- **WHEN** `DRIVER_MAX_REVIEW_ROUNDS` is set to 1
- **THEN** a second `needs-changes` verdict marks the PR needs-human

### Requirement: Needs-human terminal state

A needs-human PR is terminal for the driver: it SHALL NOT dispatch fixes,
re-reviews, or merges for that PR. The driver SHALL only resume after an
explicit human reset (state entry cleared or reset out-of-band).

#### Scenario: needs-human stops the auto-loop

- **WHEN** a PR is marked needs-human
- **THEN** the driver SHALL dispatch no further fix, re-review, or merge for it
- **AND** SHALL keep it suppressed even if the developer pushes new commits or
  reviewers later post `approve`

#### Scenario: human reset resumes the driver

- **WHEN** a human clears or resets the PR's needs-human state
- **THEN** the driver SHALL resume normal rule evaluation for that PR

### Requirement: Escalation is durable and human-visible

When the cap is reached, the driver SHALL record the escalation where humans
read it: a needs-human comment on the PR and, for ticket-bound PRs, a
needs-human dispatch to tech-pm so the Linear ticket moves to the team's
needs-human/Blocked state with an explanatory comment. All side effects SHALL
be best-effort and SHALL NOT crash the driver or block other PRs.

#### Scenario: cap-reached PR gets a needs-human comment

- **WHEN** the driver marks a PR needs-human
- **THEN** it SHALL post a PR comment stating the ticket, the completed rounds,
  and that a human must intervene

#### Scenario: the driver's own comment is not a verdict

- **WHEN** the driver posts the needs-human comment
- **THEN** the comment SHALL carry a machine sentinel the parser ignores
- **AND** the comment SHALL parse to no reviewer and no verdict

#### Scenario: ticket-bound PR escalates to tech-pm

- **WHEN** a needs-human PR is bound to a Linear ticket
- **THEN** the driver SHALL dispatch a needs-human task to tech-pm with the
  ticket id
- **AND** tech-pm SHALL move the ticket to the needs-human/Blocked state and
  comment it, starting with `Needs human:`

#### Scenario: escalation side effects are best-effort

- **WHEN** the needs-human PR comment or the tech-pm dispatch fails
- **THEN** the driver SHALL log the failure
- **AND** SHALL continue processing other PRs

### Requirement: Backward-compatible state

State files written by earlier driver versions SHALL keep working: a PR entry
without `rounds` or `needs_human` SHALL behave as `rounds: 0` and
`needs_human: false`.

#### Scenario: pre-existing state file

- **WHEN** the driver runs against a state file that predates this change
- **THEN** every PR entry is treated with zero completed rounds and no
  needs-human mark
