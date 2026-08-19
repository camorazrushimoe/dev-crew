# Environment

You own the dev and staging clusters.

## Topology

| Service | Host port | Container (crew network) |
|---|---|---|
| postgres-dev | 5433 | postgres-dev:5432 |
| postgres-staging | 5434 | postgres-staging:5432 |
| neo4j-dev | 7475 / 7688 | neo4j-dev:7687 |
| neo4j-staging | 7476 / 7689 | neo4j-staging:7687 |

All reachable over the `crew` network by service name.

## Health check

- Postgres: run `SELECT 1` against `$DEV_POSTGRES_URL` / `$STAGING_POSTGRES_URL`.
- Neo4j: reach the bolt port on `$DEV_NEO4J_URI` / `$STAGING_NEO4J_URI`.

## Config changes

- Change environment config via environment variables; document what changed.
- Never store secrets in the workspace or commit them.
