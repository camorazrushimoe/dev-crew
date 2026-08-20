# Deploy

Deploy only reviewed + merged code to `staging-env` (pre-prod).

## Workflow

1. **Confirm the request**: which project, what change (merged PR), and the target (`staging-env`).
2. **Run migrations**: apply the project's migrations to the staging database first.
3. **Deploy the service**: start/update the service on `staging-env`.
4. **Verify**: health-check the service, confirm the schema is correct.
5. **Report**: explicit status — what was deployed, where, and the verification result.

## Environment connection

You deploy to `staging-env` (`dev-crew-staging-env`). Project services are
reachable by their service name on that network (e.g. `app-staging`, `db-staging`).
`dev-env` is the developer's sandbox — the developer deploys there; you do not.

Connection strings and credentials come from the PROJECT (its README / `.env`),
NOT from the foundation. Read them from `workspace/<project>/` before deploying.

The database engine is the project's choice (SQLite, PostgreSQL, Neo4j, …).
Apply the project's declared migration tooling to its declared engine; do not
assume Postgres.

## Rules

- Never deploy an unmerged branch or unreviewed code.
- Migrations must be idempotent (safe to re-run).
- Always verify after a change; report the result explicitly.
- Never commit secrets; secrets come from the environment.
