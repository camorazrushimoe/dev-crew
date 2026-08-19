# Environments

## ADDED Requirements

### Requirement: Generic, project-agnostic environments

The foundation SHALL provide two isolated, empty networks per instance:

- `dev-env` — the dev/CI environment
- `staging-env` — the pre-production environment

These SHALL be declared by the foundation compose file with a stable, explicit
`name:` and SHALL start empty (no services, no databases).

#### Scenario: foundation provides no project services

- **WHEN** a new instance is started
- **THEN** `dev-env` and `staging-env` SHALL exist as empty networks
- **AND** the foundation SHALL NOT define any database or application service in them

### Requirement: Agents reach both environments

Every engineering agent (`developer`, `qa`, `tech-pm`, `devops`) SHALL be
attached to the `crew` network (bus + agent-to-agent) AND to both `dev-env` and
`staging-env` (project services).

#### Scenario: an agent reaches a project service

- **WHEN** a project service is running on `dev-env` or `staging-env`
- **THEN** an agent attached to that network SHALL reach it by service name

### Requirement: Project brings its own compose

Each project SHALL provide its own `workspace/<project>/compose.yml` declaring
the services it needs, attached to `dev-env` and/or `staging-env` as external
networks (`external: true`).

#### Scenario: project declares its own services

- **WHEN** a project is onboarded
- **THEN** it SHALL declare its services in its own compose file
- **AND** SHALL attach them to `dev-env` / `staging-env` via `external: true`

### Requirement: Service naming convention

Project services SHALL use the `-dev` / `-staging` suffix to distinguish the same
service across environments (e.g. `postgres-dev` on `dev-env`, `postgres-staging`
on `staging-env`).

#### Scenario: same service in both environments

- **WHEN** a project runs the same service in dev and staging
- **THEN** the dev instance SHALL be named `<service>-dev` on `dev-env`
- **AND** the staging instance SHALL be named `<service>-staging` on `staging-env`

### Requirement: Connection info lives in the project

Connection strings and credentials for project services SHALL live in the
project (its README / `.env`), NOT in the foundation. The foundation SHALL NOT
inject project-specific connection env vars into agents.

#### Scenario: no project-specific env in foundation

- **WHEN** a project is onboarded
- **THEN** the foundation SHALL NOT add project-specific connection variables
  (e.g. `DEV_POSTGRES_URL`) to any agent's environment

### Requirement: Devops owns the project environment lifecycle

Devops SHALL own the project environment lifecycle: bring up
`workspace/<project>/compose.yml` in the target network, seed base data, run
health checks, and report. Other agents SHALL NOT mutate environments directly.

#### Scenario: environment onboarding

- **WHEN** a project is onboarded
- **THEN** devops SHALL bring up the project's compose in `dev-env`, seed base
  data, and verify health
- **AND** SHALL repeat in `staging-env` when a release candidate is ready

#### Scenario: other agents do not mutate env

- **WHEN** a non-devops agent needs a deployment or config change
- **THEN** it SHALL request it from devops
- **AND** SHALL NOT touch the environment directly

## Notes

- The `crew` network remains for agents + Redis `shared-memory` and
  agent-to-agent communication.
- Project database engines (Postgres, Neo4j, etc.) are project-level services,
  not foundation concerns.
