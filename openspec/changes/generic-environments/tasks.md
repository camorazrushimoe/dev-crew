## 1. Compose — networks
- [ ] 1.1 Add `dev-env` and `staging-env` bridge networks with an explicit `name:` (e.g. `dev-crew-dev-env`, `dev-crew-staging-env`) so projects can attach via `external: true` by a stable name.
- [ ] 1.2 Attach `developer`, `qa`, `devops` to `crew` + `dev-env` + `staging-env`; keep `tech-pm` on `crew` only.

## 2. Compose — remove hardcoded DB
- [ ] 2.1 Remove the `postgres-dev`, `postgres-staging`, `neo4j-dev`, `neo4j-staging` services.
- [ ] 2.2 Remove their volumes (`postgres-dev-data`, `postgres-staging-data`, `neo4j-dev-data`, `neo4j-staging-data`).
- [ ] 2.3 Remove `DEV_POSTGRES_URL`, `STAGING_POSTGRES_URL`, `DEV_NEO4J_URI`, `DEV_NEO4J_AUTH`, `STAGING_NEO4J_URI`, `STAGING_NEO4J_AUTH` env vars from all agent services.
- [ ] 2.4 Grant the `devops` container host-Docker access (mount `/var/run/docker.sock` read-only, ensure the Docker CLI is present) so it can bring up project compose files.

## 3. Instance config
- [ ] 3.1 Drop the `DEV_*` / `STAGING_*` password variables from `.env.example`.

## 4. Docs
- [ ] 4.1 Replace the "Universal clusters" section in `docs/architecture.md` with the generic environments model.
- [ ] 4.2 Update `README.md` (cluster table + quick start) to reflect generic environments.

## 5. Devops role
- [ ] 5.1 Update `agents/devops/hermes-home/SOUL.md` — devops owns the project environment lifecycle (onboarding recipe pointer).
- [ ] 5.2 Rewrite `agents/devops/skills/environment/SKILL.md` — topology is network-based (no fixed DB services), with the onboarding recipe.
- [ ] 5.3 Rewrite `agents/devops/skills/deploy/SKILL.md` — connection info comes from the project, not foundation env vars.

## 6. Verification
- [ ] 6.1 `docker compose config` validates with no errors.
- [ ] 6.2 `docker compose up -d` brings up agents + Redis + two empty networks, with no DB services.
- [ ] 6.3 A scratch project compose attached via `external: true` is reachable by an agent over `dev-env`.

## 7. Follow-up (separate change, project-level)
- [ ] 7.1 Migrate community-intelligence to its own `compose.yml` (Postgres/Neo4j on `dev-env`/`staging-env`).
