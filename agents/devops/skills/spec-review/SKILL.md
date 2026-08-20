---
name: spec-review
description: "Review OpenSpec changes adversarially through the infrastructure lens; post a verdict."
version: 1.1.0
author: dev-crew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [OpenSpec, Spec-Review, Adversarial, DevOps, Infrastructure]
    related_skills: [deploy, environment, github-issues]
---

# Spec Review — Infrastructure lens (devops)

The factory is spec-first (OpenSpec): **no spec → no work**. Every new spec/change
is reviewed adversarially BEFORE planning or implementation. This skill is the
devops lens: you review for infrastructure impact and post an evaluation —
evaluation only, never a redesign proposal.

## When to Use

- A new OpenSpec change lands and devops is named on the review gate issue.
- You are asked to review `openspec/changes/<name>/` through the infrastructure
  lens.

## Workflow

1. Read the change directory `openspec/changes/<name>/`: `proposal.md`,
   `design.md`, `tasks.md`, and every `specs/*/spec.md`.
2. Read the repo state: is it spec-only (no `compose.yml`/`Dockerfile`/`src/`)
   or already deployed? Check via `search_files (target='files')` for
   `compose.yml`, `Dockerfile`, `src/`, and run `git log`.
3. Read the project `README.md` + `openspec/config.yaml` for the declared stack.
4. Read the target GitHub issue (title + body) — it names the exact verdict
   format and the per-agent lens list.
5. Review through the infrastructure lens; separate blocking vs non-blocking.
6. Post the review as a comment on the issue (see below).
7. Verify the comment landed (HTTP 201 + comment id, then read it back).

## The core principle: technology is the project's choice

The foundation is **project-agnostic**. It provides empty `dev-env`/`staging-env`
networks and a Redis message bus — and **no fixed database**. A project may choose
SQLite, PostgreSQL, Neo4j, DuckDB, an in-memory store, or anything else. Your
review SHALL accept whatever engine the project explicitly declares, and SHALL NOT
require a specific engine (Postgres, Redis, etc.) as a precondition for approval.

You flag the project for *gaps in its own declared stack*, not for picking a
"wrong" technology. A SQLite project that names its engine, migration path and
deploy packaging is just as approvable as a Postgres one.

## Verdict format (match the issue's requested shape)

- **Verdict:** `approve` | `needs-changes` | `N/A`
- **Blocking (max 3):** must be resolved before work starts
- **Non-blocking:** nice-to-have → backlog
- `N/A` only when the spec has zero impact on your lens.

## Infrastructure lens (devops) — checklist

Review for: new services/dependencies, what is not yet deployed, what could break
at deploy time. Check each item against the factory deployment model (see the
`environment` skill):

- **Justify any heavy topology first.** Ask: does this design actually need a
  client-server DB or a distributed queue? A single-process bot with SQLite +
  in-process APScheduler does NOT. Only require Postgres/Redis/broker when the
  design calls for them (multi-instance, Celery workers, shared rate-limit/lock
  store). Otherwise flag "upgrade path to Postgres/Redis if you scale out" as a
  non-blocking note — never a must-provision-now blocker.
- **Persistence is declared and provisionable.** The project must NAME a concrete
  database engine (SQLite, Postgres, Neo4j, …) and a way to provision it — either
  in its own `workspace/<project>/compose.yml` (server DBs) or in-process (SQLite
  / file-based). A spec that needs persistence but names no engine, or marks
  packaging "optional" with no committed compose, means nothing is deployable →
  blocking. This is about *missing provisioning*, NOT about the engine choice.
- **Migration story exists.** A bare "Migrations" task with no named tool or
  strategy means idempotent schema changes can't be applied before deploy →
  blocking. The tool must fit the chosen engine (e.g. Alembic + SQLAlchemy for
  Postgres or SQLite, or SQLite's built-in schema management). Do NOT assume
  `asyncpg` — that is Postgres-only.
- **Service/queue topology pinned.** "APScheduler / Celery / Redis" as an open
  choice changes the service graph (in-process = 1 service; Celery = worker +
  broker). Unresolved topology → blocking (can't provision the right services).
- **Secrets / external deps provisioned.** Required env vars and any new SaaS
  egress (e.g. OpenAI) must be accounted for.
- **Health/readiness signal.** A `/healthz` or Docker `HEALTHCHECK` enables
  verify-after-change.
- **Single-instance assumptions** (e.g. scheduler double-send risk on scale-out)
  → non-blocking.

## Posting the review to GitHub

Prefer `gh issue comment N --body "$(cat review.md)"` (see `github-issues`
skill). If `gh` is not installed, fall back to the REST API — the token lives in
`$HERMES_HOME/.env`:

```bash
set -a && . "$HERMES_HOME/.env" && set +a          # GITHUB_TOKEN lives here
python3 -c "import json; json.dump({'body': open('review.md').read()}, open('comment.json','w'))"
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  --data-binary @comment.json \
  "https://api.github.com/repos/OWNER/REPO/issues/N/comments"
```

Expect HTTP `201` + a comment `id`; then GET the comment and confirm the verdict
line and body length are intact.

## Pitfalls

- Do NOT propose a redesign — evaluation only (blocking/non-blocking findings).
- Do NOT require a specific database engine. The engine is the project's choice.
- Cap blocking at 3 even when more issues exist; demote the rest to non-blocking.
- `N/A` is only for genuine zero impact. A spec adding DB/scheduler/external SaaS
  has impact.
- Read the issue body first — it states the exact verdict format and lens list.

See `references/infra-review-example.md` for a canonical worked example (blocking
vs non-blocking findings, phrasing, and posted format).
