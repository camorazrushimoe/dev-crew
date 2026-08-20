# Worked example — infrastructure review of a greenfield bot spec

Canonical example of the infrastructure lens applied to a spec-only repo. Use as a
phrasing/template reference; the exact findings generalize to any spec-first project
that adds persistence + a background scheduler + external LLM SaaS. The database
engine below is whatever the project declared — this template works identically for
SQLite, Postgres, or any other engine.

## Repo state that drove the verdict

- Spec-only: no `compose.yml`, no `Dockerfile`, no `src/` — nothing deployable.
- The project declared a DB + scheduler, but marked packaging "optional" and left
  the scheduler/queue and migration tool as open choices.

## Verdict: `needs-changes`

Three blocking findings (the recurring trio for greenfield specs):

1. **No deploy packaging — packaging "optional" conflicts with the factory model.**
   Factory deploys via `workspace/<project>/compose.yml` on the `dev-env`/`staging-env`
   external networks; the foundation provides no fixed services. With no committed
   compose and no service topology there is nothing to deploy. The project's own
   declared services (app + its DB + any queue) must be committed and made required.
   This is *not* a demand to use a specific DB — it is a demand that the chosen DB
   actually be provisioned.

2. **Scheduler/queue topology unresolved.** In-process scheduler = one long-running
   service; a Celery-style worker = a separate worker + broker. Changes which services
   to provision. Must be locked before implementation.

3. **Migration tooling unspecified.** A bare "Migrations" task with no named tool or
   strategy means idempotent schema changes can't be applied first. The tool must fit
   the declared engine (e.g. Alembic for Postgres/SQLite, or SQLite's built-in schema
   management). Flag the *missing tool*, never the engine choice.

## Non-blocking (backlog) — the recurring list

- Single-instance assumption for the proactive scheduler (no distributed claim →
  double-send on scale-out). Fine for MVP; document it.
- External secrets must be provisioned pre-deploy (any API keys = new SaaS egress
  dependency).
- No health/readiness signal (`/healthz` or Docker `HEALTHCHECK`) for
  verify-after-change.

## Posted format

Header: `## DevOps — Infrastructure review` → `**Verdict:** `needs-changes`` →
`### Blocking (must resolve before work starts)` (numbered, ≤3) →
`### Non-blocking (backlog)` (bulleted).
