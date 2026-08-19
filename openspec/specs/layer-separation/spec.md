# Layer Separation

## ADDED Requirements

### Requirement: Three layers never mix

The factory SHALL keep three layers strictly separated:

| Layer | Location | Git |
|---|---|---|
| Foundation (template) | this repo | tracked |
| Instance config | per-machine files | gitignored |
| Project work | outside the repo | own git |

### Requirement: Foundation contents

The foundation SHALL contain identity (`agents/<name>/hermes-home/SOUL.md`),
capabilities (`agents/<name>/skills/`), team + infra (`docker-compose.yml`),
protocol (`crew/`, `bus/`), and docs (`docs/`, `README.md`). It SHALL be
versioned and updated by `git pull`.

### Requirement: Instance config contents

Instance config SHALL hold secrets and addresses that differ per machine:
`.env` (cluster passwords), `tokens/tokens.yaml`, and `crew/agents.json` (door
secrets). These SHALL be gitignored and never committed.

### Requirement: Project work contents

Project work SHALL live outside the foundation: `workspace/<project>/` (its own
git repo), cluster data (its own schema/DB), and a separate Linear project.

#### Scenario: a foundation upgrade does not touch project work

- **WHEN** the foundation is updated (PR merged, then `git pull` on the instance)
- **THEN** `workspace/`, cluster data, and Linear projects SHALL be untouched

### Requirement: Agent context assembly

An agent's context SHALL be assembled from the layers:
WHO it is (`SOUL.md`), WHAT it can do (skills), WHERE the infra is (env vars),
and WHAT to do now (the Linear ticket). Nothing project-specific SHALL be baked
into the foundation.
