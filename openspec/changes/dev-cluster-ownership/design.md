# Design: developer-owned dev cluster

## Ownership model

| Environment | Network (compose name) | Owner | Purpose |
|---|---|---|---|
| `dev-env` | `dev-crew-dev-env` | **developer** | sandbox — build, `docker compose up`, test, iterate, break freely |
| `staging-env` | `dev-crew-staging-env` | **devops** | pre-prod gate — only merged, reviewed code; QA verifies here |

The `crew` network stays agents + Redis `shared-memory` only.

## Pipeline (before → after)

**Before:** merge → devops deploy `dev-env` → QA test → QA approve → devops deploy
`staging-env`.

**After:** developer verifies on `dev-env` **before** the PR → PR → review → merge →
devops deploy `staging-env` → QA test → QA approve.

The developer's dev-env activity is informal (like a local Docker), not a pipeline
stage. The formal gate is staging only.

## Key decisions

1. **Shared host daemon, not DinD.** `dev-env` and `staging-env` are two networks on
   the single host Docker daemon (as today). Separation is by network name + SOUL
   rules, not hard isolation. Caveat (accepted): with the same socket, the developer
   *technically* could reach staging — enforced by convention for now; a socket proxy
   or DinD is a later hardening (separate issue).
2. **Compose plugin.** The base image `nousresearch/hermes-agent:latest` lacks the
   compose plugin. Plan: a thin custom image (`FROM hermes-agent` + install
   docker-compose-plugin) used by `developer` and `devops`, OR a boot-time install of
   the plugin binary. (Implementation task — see tasks.md.)
3. **Who gets `docker.sock`:** `developer` (for `dev-env`) and `devops` (for
   `staging-env`). `qa` does NOT deploy — it tests over the network (it is already
   attached to both env networks). `tech-pm` — no.
4. **Keep network names** (`dev-env` / `staging-env`), redefine semantics. No rename
   to "Dev Cluster"/"Pre-Prod" to avoid churn (the terms are used as labels only).
5. **Promotion between envs.** The same project `compose.yml` must attach to `dev-env`
   (developer) or `staging-env` (devops). Mechanism: a network name driven by an env
   var (e.g. `SPACEDBRO_NETWORK`) or an override file (`compose.staging.yml`).

## Non-goals

- DinD per environment, socket proxy, RBAC on the daemon — deferred (separate issues).
- Any change to how QA runs tests (only *where*: staging instead of dev).
