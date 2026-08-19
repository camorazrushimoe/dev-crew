# Environment

You own the dev and staging environments end-to-end.

## Topology

The foundation provides two empty, project-agnostic networks:

| Network | Compose name | Purpose |
|---|---|---|
| dev-env | `dev-crew-dev-env` | dev/CI — developer builds and breaks freely |
| staging-env | `dev-crew-staging-env` | pre-prod — qa verifies release candidates |

The `crew` network is for agents + Redis `shared-memory` only. No project
services run on `crew`.

Projects bring their own services via `workspace/<project>/compose.yml` and
attach to these networks with `external: true`. There are NO fixed database
services in the foundation.

## Onboarding a project environment

1. Read `workspace/<project>/compose.yml` (and the project's own README for
   connection info and seed steps).
2. Bring it up against the host Docker daemon (the socket is mounted read-only
   at `/var/run/docker.sock`):
   - `docker compose -f /workspace/<project>/compose.yml up -d`
   - If the `compose` plugin is missing in this container, use plain `docker`
     commands or ask the manager to run compose from the host.
3. Seed base data if the project defines a seed step.
4. Health-check the services and report explicitly.

## Health check

- Reach each project service on `dev-env` / `staging-env` by its service name
  (e.g. `postgres-dev`), using the connection info from the project.

## Config changes

- Change environment config via environment variables; document what changed.
- Never store secrets in the workspace or commit them.
