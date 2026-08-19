## Context

The foundation must provide isolated test environments WITHOUT hardcoding what
runs in them. Environments are network namespaces; projects bring their own
services via their own compose file.

## Goals

- Foundation stays project-agnostic: no database engines baked in.
- Projects can run any service (Postgres, Neo4j, a Node bot, or nothing).
- `dev-env` and `staging-env` remain isolated from each other.
- Devops has a deterministic recipe for onboarding a project's environment.

## Non-Goals

- No per-project orchestration inside the foundation (no `profiles` per project).
- No change to agent-to-agent communication (`crew` network + bus stay as-is).

## Approach

### Networks

The foundation compose declares three bridge networks:

- `crew` — agents + Redis `shared-memory` (unchanged).
- `dev-env` — empty, for project dev/CI services.
- `staging-env` — empty, for project pre-production services.

Agents attach to all three. A project's compose attaches its services to
`dev-env` and/or `staging-env` via `external: true`.

**Naming gotcha:** Compose prefixes network names with the project name (e.g.
`dev-crew_dev-env`). To let project compose files attach by a stable name, the
foundation SHALL set an explicit `name:` on each env network (e.g.
`name: dev-crew-dev-env`). The project then declares the network with
`external: true` and the same name.

### Why `external: true` over `profiles`

`profiles` would keep every project's services inside the foundation's single
compose file, forcing the foundation to know about every project (violates
layer-separation). `external: true` keeps each project in its own compose file
while sharing the env networks by name.

### Service naming

A single project compose file runs dev and staging side by side, so service
names must be unique across the two networks an agent sees. Convention:
`<service>-dev` on `dev-env`, `<service>-staging` on `staging-env`.

### Connection info

The foundation stops injecting `DEV_POSTGRES_URL`, `STAGING_POSTGRES_URL`,
`DEV_NEO4J_URI`, `STAGING_NEO4J_URI`, and the matching `*_AUTH` vars. Each
project documents its own connection strings; agents read them per-task from
the project context.

### Devops recipe (project environment onboarding)

Lives in devops `SOUL.md` + the `environment` skill:

1. Read `workspace/<project>/compose.yml`.
2. `docker compose -f <project>/compose.yml up -d` (services join `dev-env` / `staging-env`).
3. Seed base data if the project defines a seed step.
4. Health-check the services and report explicitly.

### Migration of community-intelligence (follow-up)

community-intelligence currently relies on the foundation's `postgres-dev` /
`neo4j-dev`. After this change it SHALL carry its own
`workspace/community-intelligence/compose.yml` declaring `postgres-dev`,
`postgres-staging`, `neo4j-dev`, `neo4j-staging` on the respective networks.
This is a separate project-level change, listed here so the two move together.

## Risks / Notes

- Agents attaching to three networks slightly increases their surface; acceptable.
- Redis `shared-memory` stays on `crew` only (project-agnostic bus).
- The dashboard and action-schema gaps (devops not tracked / not an actor) are separate changes.
