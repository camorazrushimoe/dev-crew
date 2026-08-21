# Message Bus

## ADDED Requirements

### Requirement: Shared memory service

The factory SHALL run a Redis service (`shared-memory`, Redis 7) as the common
message bus / action registry shared by all agents.

### Requirement: Action envelope

Messages on the bus SHALL follow the envelope in `bus/action-schema.json`:

- `id` (string, UUID) — required
- `actor` (string, `developer` | `qa` | `tech-pm` | `devops` | `orchestrator`) — required
- `action` (string) — required
- `target` (string) — required, agent id or `*` (broadcast)
- `timestamp` (string, ISO 8601) — required
- `payload` (object) — optional

The JSON Schema in `bus/action-schema.json` is the authoritative enum for
`actor`. Spec and schema SHALL stay in sync.

Known action types include (non-exhaustive):

- `task.created`, `task.started`, `task.finished`, `task.stale`
- `pr.opened`, `review.requested`
- `bug.found`
- `skill.created`, `skill.patched`
- `test.failed`, `memory.write`

#### Scenario: broadcast to all agents

- **WHEN** an action has `target` = `*`
- **THEN** it SHALL be treated as a broadcast to all agents

#### Scenario: completion and skill events are first-class

- **WHEN** a task finishes or a skill is created/patched
- **THEN** the corresponding action (`task.finished`, `skill.created`, or
  `skill.patched`) SHALL be publishable on the bus under the standard envelope

### Requirement: Bus is a signal layer, not the record

The bus SHALL carry signals and notifications. The persistent record of task
decisions SHALL be Linear ticket comments, not the bus.

#### Scenario: a decision is recorded durably

- **WHEN** a task decision is made
- **THEN** it SHALL be written to Linear ticket comments
- **AND** the bus SHALL only signal that a decision happened
