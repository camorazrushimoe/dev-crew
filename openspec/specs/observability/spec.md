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

### Requirement: Run-supervision view

The factory SHALL provide a per-run supervision surface (dashboard page or CLI)
where a **run** is a Linear Project. For the selected run the view SHALL show:

- per ticket: state, linked PR (if any), assigned agent
- per agent: current task, state (idle/working/down), last activity
- cost: token usage per agent and/or ticket when available from Hermes logs or state

#### Scenario: manager opens one page for the current run

- **WHEN** the manager selects a Linear Project as the active run
- **THEN** the supervision view SHALL list the project's tickets with states and assignees
- **AND** SHALL show which agents are working on which tickets
- **AND** SHALL surface available token-cost information without requiring manual log stitching

#### Scenario: supervision uses existing data sources

- **WHEN** the run-supervision view is rendered
- **THEN** it SHALL aggregate from Linear (tickets/project), GitHub (linked PRs),
  Redis status keys, and agent activity/cost sources already present in the factory

## Notes

The basic health dashboard currently tracks `developer`, `qa`, and `tech-pm`.
Tracking for `devops` remains a known gap. Run-supervision builds on top of the
health view and does not replace it.
