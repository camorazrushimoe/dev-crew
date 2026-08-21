# Task Completion

## ADDED Requirements

### Requirement: Deterministic completion signal

Task start and finish SHALL be signalled by the runtime (preferred: thin wrapper
around the door handler; Hermes hook is an acceptable alternative), not by LLM
discretion in the agent prompt. The signal SHALL fire even if the agent does not
write its own final message.

#### Scenario: task finish produces a structured push

- **WHEN** an agent finishes a dispatched task (success or failure)
- **THEN** the runtime SHALL emit a structured completion payload
  (`agent`, `ticket`, `status`, `summary`, optional `run`)
- **AND** SHALL post an auto-comment on the Linear ticket with the result
- **AND** SHALL move the Linear ticket state per the state rules below
- **AND** SHALL ping the manager via a webhook / door callback

#### Scenario: task start is recorded on the bus

- **WHEN** an agent begins work on a dispatched task that has a bound ticket
- **THEN** the runtime SHALL emit a bus action `task.started`
- **AND** MAY move the Linear ticket to In Progress and post a short start comment

### Requirement: Ticket binding

Every dispatched task that participates in completion signalling SHALL carry a
Linear ticket identifier in the door message (e.g. `Ticket BON-27 — ...`). The
runtime SHALL bind start/finish events to that identifier.

#### Scenario: finish without a ticket id

- **WHEN** an agent finishes work that was not dispatched with a ticket identifier
- **THEN** the runtime SHALL still emit `task.finished` on the bus with
  `ticket` set to null / omitted
- **AND** SHALL NOT attempt a Linear state move
- **AND** SHALL still attempt the manager ping with the structured payload

### Requirement: Linear state rules on finish

When a ticket is bound, the runtime SHALL choose the Linear state as follows:

| `status` in payload | Linear state |
|---|---|
| `success` | **In Review** if the task produced a PR or reviewable artifact; otherwise **Done** |
| `failure` | **Blocked** (or the team's equivalent blocked/failed state) |
| `blocked` | **Blocked** |

The payload `status` SHALL be set by the runtime from the agent turn outcome
(successful completion vs error/abort), not by free-form LLM text alone.

#### Scenario: successful implementation with a PR

- **WHEN** the developer finishes a ticket-bound task that opened a PR
- **THEN** the Linear ticket SHALL move to In Review

#### Scenario: failed or aborted task

- **WHEN** the agent turn ends in error or explicit abort
- **THEN** `status` SHALL be `failure` or `blocked`
- **AND** the Linear ticket SHALL move to Blocked when a ticket is bound

### Requirement: Best-effort external side effects

Linear comments, Linear state moves, and manager webhooks SHALL be best-effort.
Failure of an external side effect SHALL NOT crash or block the agent process.

#### Scenario: Linear is unreachable on finish

- **WHEN** a task finishes and Linear API calls fail
- **THEN** the runtime SHALL still publish `task.finished` on the bus
- **AND** SHALL log the Linear failure
- **AND** SHALL NOT terminate or hang the agent container

#### Scenario: manager webhook is unreachable

- **WHEN** a task finishes and the manager webhook fails
- **THEN** the runtime SHALL still publish `task.finished` on the bus
- **AND** SHALL log the webhook failure
- **AND** SHALL NOT terminate or hang the agent container

### Requirement: Bus actions for lifecycle

The runtime SHALL publish bus actions:

- `task.started` — agent began work on a ticket-bound task
- `task.finished` — agent completed (success, failure, or blocked)
- `task.stale` — agent silent for longer than the configured threshold on an assigned task

#### Scenario: finish is visible on the bus

- **WHEN** a task finishes
- **THEN** a `task.finished` action SHALL appear on the shared-memory bus with the structured payload

### Requirement: Stale-task signal

If an agent is silent for N minutes (configurable; default recommended: 30) while
assigned to a task, the runtime SHALL emit `task.stale` and MAY comment on the
Linear ticket when a ticket is bound.

#### Scenario: silent agent is flagged

- **WHEN** an agent has been silent longer than the threshold on an assigned task
- **THEN** a `task.stale` action SHALL be published
- **AND** the manager SHALL be able to see the stale signal without polling logs

### Requirement: No reliance on prompt-level reporting alone

SOUL.md and skills MAY still instruct agents to comment when done, but the
factory SHALL NOT depend on that for the manager-facing completion signal.

#### Scenario: agent skips its own final comment

- **WHEN** the agent finishes without writing a Linear comment
- **THEN** the runtime completion path SHALL still attempt the auto-comment and manager ping (best-effort)
