# Deploy

Deploy only reviewed + merged code to the clusters.

## Workflow

1. **Confirm the request**: which project, which environment (dev/staging), what change.
2. **Run migrations**: apply the project's migrations to the target Postgres cluster first.
3. **Deploy the service**: start/update the service against the target cluster.
4. **Verify**: health-check the service and DB, confirm the schema is correct.
5. **Report**: explicit status — what was deployed, where, and the verification result.

## Cluster connection

- dev Postgres:      `$DEV_POSTGRES_URL`     (postgres-dev:5432)
- staging Postgres:  `$STAGING_POSTGRES_URL` (postgres-staging:5432)
- dev Neo4j:         `$DEV_NEO4J_URI`        (neo4j-dev:7687)
- staging Neo4j:     `$STAGING_NEO4J_URI`    (neo4j-staging:7687)

## Rules

- Never deploy an unmerged branch or unreviewed code.
- Migrations must be idempotent (safe to re-run).
- Always verify after a change; report the result explicitly.
- Never commit secrets; secrets come from the environment.
