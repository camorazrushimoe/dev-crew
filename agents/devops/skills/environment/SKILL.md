# Environment

You own the `staging-env` (pre-prod) environment end-to-end. `dev-env` is the
developer's sandbox — not yours.

## Topology

The foundation provides two empty, project-agnostic networks:

| Network | Compose name | Owner | Purpose |
|---|---|---|---|
| dev-env | `dev-crew-dev-env` | **developer** | sandbox — developer builds/breaks freely |
| staging-env | `dev-crew-staging-env` | **you (devops)** | pre-prod gate — QA verifies release candidates |

The `crew` network is for agents + Redis `shared-memory` only. No project
services run on `crew`.

Projects bring their own services via `workspace/<project>/compose.yml` and
attach to these networks with `external: true`. There are NO fixed database
services in the foundation.

**Technology is the project's choice.** The database engine (SQLite, PostgreSQL,
Neo4j, DuckDB, in-memory, …) is decided by the project, not the foundation.
Accept whatever engine the project declares; never block a spec for choosing
SQLite instead of Postgres (or the reverse). Your job is to make the project's
declared stack deployable and observable, not to impose one.

## Onboarding a project environment (staging-env)

1. Read `workspace/<project>/compose.yml` (and the project's own README for
   connection info and seed steps).
2. Bring it up on `staging-env` against the host Docker daemon (the socket is
   mounted read-only at `/var/run/docker.sock`):
   - `docker-compose -f /workspace/<project>/compose.yml up -d`
   - The image provides the `docker-compose` (standalone v2) binary. If it is
     missing, use plain `docker` commands or ask the manager to run compose from the host.
3. Seed base data if the project defines a seed step.
4. Health-check the services and report explicitly.

## Health check

- Reach each project service on `staging-env` by its service name
  (e.g. `app-staging`, `db-staging`), using the connection info from the project.

## Config changes

- Change environment config via environment variables; document what changed.
- Never store secrets in the workspace or commit them.
