# Task Completion

## ADDED Requirements

### Requirement: Deterministic completion signal

Task start and finish SHALL be signalled by the runtime (Hermes hook or door
wrapper), not by LLM discretion in the agent prompt. The signal SHALL fire even
if the agent does not write its own final message.

#### Scenario: task finish produces a structured push

- **WHEN** an agent finishes a dispatched task (success or failure)
- **THEN** the runtime SHALL emit a structured completion payload
  (`agent`, `ticket`, `status`, `summary`, optional `run`)
- **AND** SHALL post an auto-comment on the Linear ticket with the result
- **AND** SHALL move the Linear ticket state (Done / In Review / Blocked as appropriate)
- **AND** SHALL ping the manager via a webhook / door callback

#### Scenario: task start is optionally recorded

- **WHEN** an agent begins work on a dispatched task
- **THEN** the runtime MAY move the Linear ticket to In Progress and post a short start comment
- **AND** SHALL emit a bus action `task.started`

### Requirement: Bus actions for lifecycle

The runtime SHALL publish bus actions:

- `task.started` — agent began work on a ticket
- `task.finished` — agent completed (success or failure)
- `task.stale` — agent silent for longer than the configured threshold on an assigned task

#### Scenario: finish is visible on the bus

- **WHEN** a task finishes
- **THEN** a `task.finished` action SHALL appear on the shared-memory bus with the structured payload

### Requirement: Stale-task signal

If an agent is silent for N minutes (configurable) while assigned to a task, the
runtime SHALL emit `task.stale` and MAY comment on the Linear ticket.

#### Scenario: silent agent is flagged

- **WHEN** an agent has been silent longer than the threshold on an assigned task
- **THEN** a `task.stale` action SHALL be published
- **AND** the manager SHALL be able to see the stale signal without polling logs

### Requirement: No reliance on prompt-level reporting alone

SOUL.md and skills MAY still instruct agents to comment when done, but the
factory SHALL NOT depend on that for the manager-facing completion signal.

#### Scenario: agent skips its own final comment

- **WHEN** the agent finishes without writing a Linear comment
- **THEN** the runtime completion hook SHALL still post the auto-comment and manager ping
