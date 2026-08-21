# Environments

## ADDED Requirements

### Requirement: Generic, project-agnostic environments

The foundation SHALL provide two isolated, empty networks per instance:

- `dev-env` — the developer sandbox ("Dev Cluster")
- `staging-env` — the pre-prod gate (QA-verified)

These SHALL be declared by the foundation compose file with stable, explicit
names (`dev-crew-dev-env` and `dev-crew-staging-env`) and SHALL start empty
(no services, no databases). Projects SHALL attach to these names via
`external: true`.

#### Scenario: foundation provides no project services

- **WHEN** a new instance is started
- **THEN** `dev-env` and `staging-env` SHALL exist as empty networks
- **AND** the foundation SHALL NOT define any database or application service in them

### Requirement: Agents reach both environments

The build/verify/deploy agents (`developer`, `qa`, `devops`) SHALL be attached
to the `crew` network (bus + agent-to-agent) AND to both `dev-env` and
`staging-env` (project services). `tech-pm` SHALL be attached to `crew` only.

#### Scenario: an agent reaches a project service

- **WHEN** a project service is running on `dev-env` or `staging-env`
- **THEN** an agent attached to that network SHALL reach it by service name

### Requirement: Project brings its own compose

Each project SHALL provide its own `workspace/<project>/compose.yml` declaring
the services it needs and its own data volumes, attached to `dev-env` and/or
`staging-env` as external networks (`external: true`).

#### Scenario: project declares its own services

- **WHEN** a project is onboarded
- **THEN** it SHALL declare its services in its own compose file
- **AND** SHALL attach them to `dev-env` / `staging-env` via `external: true`

### Requirement: Service naming convention

Project services SHALL use the `-dev` / `-staging` suffix to distinguish the same
service across environments (e.g. `app-dev` on `dev-env`, `app-staging`
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
  (e.g. `DEV_DATABASE_URL`) to any agent's environment

### Requirement: Developer owns the dev-env sandbox

`dev-env` SHALL be the developer's sandbox ("Dev Cluster"). The developer SHALL
have Docker daemon access and SHALL be able to bring up, test, iterate and tear
down its own project services on `dev-env` before opening a PR. The developer
SHALL NOT deploy to `staging-env`.

#### Scenario: developer verifies before PR

- **WHEN** a developer implements a change
- **THEN** it SHALL be able to `docker compose up` its project on `dev-env`
- **AND** SHALL verify the service is healthy before opening the PR

#### Scenario: developer cannot touch pre-prod

- **WHEN** a developer attempts to deploy to `staging-env`
- **THEN** it SHALL NOT do so
- **AND** SHALL request a staging deployment from devops

### Requirement: Devops owns the staging-env (pre-prod) gate

Devops SHALL own `staging-env` (pre-prod): bring up
`workspace/<project>/compose.yml` there, run migrations, seed base data, run
health checks, and report. Devops SHALL deploy only merged, reviewed code to
`staging-env`. QA SHALL verify release candidates on `staging-env`.

#### Scenario: environment onboarding

- **WHEN** a project is onboarded
- **THEN** devops SHALL bring up the project's compose in `staging-env`, seed
  base data, and verify health

#### Scenario: only merged code reaches staging

- **WHEN** a change is ready for `staging-env`
- **THEN** devops SHALL deploy only merged, reviewed code
- **AND** SHALL NOT deploy unreviewed or unmerged code to `staging-env`

#### Scenario: QA approves the release candidate

- **WHEN** a build is deployed to `staging-env`
- **THEN** qa SHALL verify it on `staging-env`
- **AND** SHALL approve the build explicitly

### Requirement: Database engine is the project's choice

The foundation SHALL NOT prescribe a database engine. Each project SHALL choose
its own persistence (SQLite, PostgreSQL, Neo4j, DuckDB, in-memory, etc.) and
declare it in its own compose and README. Devops SHALL accept whatever engine
the project explicitly declares and SHALL NOT require a specific engine (e.g.
Postgres) as a precondition for approving a spec.

#### Scenario: project declares a non-Postgres database

- **WHEN** a project spec explicitly declares SQLite (or any other engine) as
  its database
- **THEN** devops SHALL treat that choice as valid
- **AND** SHALL NOT flag it as blocking on the grounds that the factory "uses
  Postgres"

#### Scenario: project leaves the database unspecified

- **WHEN** a project spec requires persistence but does not name a database
  engine or its provisioning/migration path
- **THEN** devops SHALL flag the missing engine/path as a blocker
- **AND** SHALL ask the project to name the engine and how it will be
  provisioned and migrated

## Notes

- The `crew` network remains for agents + Redis `shared-memory` and
  agent-to-agent communication.
- Project database engines (SQLite, Postgres, Neo4j, DuckDB, etc.) are
  project-level services, not foundation concerns — the foundation never
  mandates a specific engine.
