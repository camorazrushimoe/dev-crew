## Why

The foundation currently hardcodes four database services (`postgres-dev`,
`postgres-staging`, `neo4j-dev`, `neo4j-staging`) into its docker-compose and
injects their connection strings into every agent's environment. This conflates
"isolated environment" with "specific database engines" — it assumes every
project is a Postgres+Neo4j application, which breaks for projects that need
neither (e.g. a standalone Node bot). The fix makes environments generic and
lets each project bring its own services.

## What Changes

- Remove the four hardcoded DB services (and their volumes) from the foundation compose.
- Add two empty networks `dev-env` and `staging-env` with stable names.
- Attach all agents to `crew` + `dev-env` + `staging-env`.
- Remove project-specific connection env vars (`DEV_POSTGRES_URL`, `DEV_NEO4J_URI`, etc.) from agent env.
- Update `.env.example` (drop the DB passwords).
- Update docs (`README.md`, `docs/architecture.md`) to the generic-env model.
- Update devops `SOUL.md` and the `environment` / `deploy` skills to the new model.
- Migrate community-intelligence's Postgres/Neo4j to its own project compose (follow-up, project-level).

## Capabilities

### New Capabilities
- `environments`: generic, project-agnostic dev/staging environments + project-compose convention.

## Impact

- `docker-compose.yml` — remove 4 DB services + volumes; add networks; change agent networks + env.
- `.env.example` — drop cluster passwords.
- `docs/architecture.md`, `README.md` — generic-env model.
- `agents/devops/hermes-home/SOUL.md` — project env lifecycle ownership + onboarding recipe.
- `agents/devops/skills/environment/SKILL.md`, `agents/devops/skills/deploy/SKILL.md` — new topology + project-provided connection info.
