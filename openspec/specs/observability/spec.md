# Observability

## ADDED Requirements

### Requirement: Live team dashboard

The factory SHALL provide an observability dashboard (`dashboard/app.py`) served
on port `8660`, showing each agent's state (`working` / `idle` / `down`) and its
current task.

### Requirement: Reporter loop

A reporter thread SHALL poll each agent's `/health` endpoint (liveness) and the
tail of its gateway log, derive the agent state, and write it to Redis keys
`status:<agent>` (with a ~10s TTL) and `activity:<agent>` (most recent events).

#### Scenario: an agent becomes unreachable

- **WHEN** an agent's `/health` endpoint is unreachable
- **THEN** the dashboard SHALL show that agent as `down`

#### Scenario: an agent is processing a task

- **WHEN** the gateway log shows an inbound message
- **THEN** the dashboard SHALL show that agent as `working` with the current task

### Requirement: HTTP API and web view

The dashboard SHALL serve `GET /api/status` (JSON with agent statuses and recent
activity) and the live web view at `/` (`index.html`).

## Notes

The dashboard currently tracks `developer`, `qa`, and `tech-pm`. Tracking for
`devops` is a known gap to be addressed in a future change.
