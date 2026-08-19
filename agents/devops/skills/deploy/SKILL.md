# Deploy

Deploy only reviewed + merged code to the environments.

## Workflow

1. **Confirm the request**: which project, which environment (dev/staging), what change.
2. **Run migrations**: apply the project's migrations to the target database first.
3. **Deploy the service**: start/update the service against the target environment.
4. **Verify**: health-check the service, confirm the schema is correct.
5. **Report**: explicit status — what was deployed, where, and the verification result.

## Environment connection

Environments are the `dev-env` (`dev-crew-dev-env`) and `staging-env`
(`dev-crew-staging-env`) networks. Project services are reachable by their
service name on the relevant network (e.g. `postgres-dev` on `dev-env`).

Connection strings and credentials come from the PROJECT (its README / `.env`),
NOT from the foundation. Read them from `workspace/<project>/` before deploying.

## Rules

- Never deploy an unmerged branch or unreviewed code.
- Migrations must be idempotent (safe to re-run).
- Always verify after a change; report the result explicitly.
- Never commit secrets; secrets come from the environment.
