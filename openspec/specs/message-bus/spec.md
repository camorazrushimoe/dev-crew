# Message Bus

## ADDED Requirements

### Requirement: Shared memory service

The factory SHALL run a Redis service (`shared-memory`, Redis 7) as the common
message bus / action registry shared by all agents.

### Requirement: Action envelope

Messages on the bus SHALL follow the envelope in `bus/action-schema.json`:

- `id` (string, UUID) — required
- `actor` (string, `developer` | `qa` | `tech-pm` | `orchestrator`) — required
- `action` (string) — required, e.g. `task.created`, `pr.opened`, `review.requested`
- `target` (string) — required, agent id or `*` (broadcast)
- `timestamp` (string, ISO 8601) — required
- `payload` (object) — optional

#### Scenario: broadcast to all agents

- **WHEN** an action has `target` = `*`
- **THEN** it SHALL be treated as a broadcast to all agents

### Requirement: Bus is a signal layer, not the record

The bus SHALL carry signals and notifications. The persistent record of task
decisions SHALL be Linear ticket comments, not the bus.

#### Scenario: a decision is recorded durably

- **WHEN** a task decision is made
- **THEN** it SHALL be written to Linear ticket comments
- **AND** the bus SHALL only signal that a decision happened
