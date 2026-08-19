# Agent Roles

## ADDED Requirements

### Requirement: Four engineering agents

The factory SHALL run four engineering agents, each in its own Docker container
with a distinct role, webhook door, and host port:

| Role | Door (host) | Owns |
|---|---|---|
| `developer` | `8651` | Implements specs as code, opens PRs |
| `qa` | `8652` | Verifies against specs, writes QA reports |
| `tech-pm` | `8653` | Decomposes specs into plans/tickets |
| `devops` | `8654` | Owns test/staging env, deploys merged code |

#### Scenario: every agent is reachable on a distinct door

- **WHEN** the factory is running
- **THEN** each role SHALL be reachable on its own host port (8651–8654)

### Requirement: Identity and capability are mounted, not baked in

Each agent SHALL load its identity from `SOUL.md` (who it is, its discipline,
and the planning-gate rules) and its capabilities from role skills mounted
read-only at `/opt/data/skills/dev-crew`.

#### Scenario: role is project-agnostic

- **WHEN** an agent boots
- **THEN** its SOUL SHALL describe only its role
- **AND** SHALL NOT contain project-specific context

### Requirement: Shared mounts

Each agent SHALL mount the shared workspace and tooling:
`hermes-home` → `/opt/data`, role skills → `/opt/data/skills/dev-crew` (read-only),
`crew/` → `/opt/crew` (read-only), `workspace/` → `/workspace`.

### Requirement: English-only output

Agents SHALL produce code, commits, PRs, tickets and reports in English.
