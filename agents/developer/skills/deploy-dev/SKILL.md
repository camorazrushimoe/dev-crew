---
name: deploy-dev
description: "Run the project on dev-env (your sandbox) and verify it before opening a PR."
version: 1.0.0
author: dev-crew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dev-env, docker, compose, verify, developer]
    related_skills: [implement, tdd, code-review]
---

# Deploy / verify on dev-env (developer sandbox)

You own `dev-env` — your sandbox ("Dev Cluster"). Bring the project up there and
verify it actually runs before you open a PR. This is your local Docker: build,
test, iterate, break freely.

## When to use

- You finished a change and want to confirm it actually boots/runs (not just passes tests).
- You need to iterate: bring up → test → change → bring up again.

## Workflow

1. Read the project's `workspace/<project>/compose.yml` and README (required env
   vars, seed steps, health endpoint).
2. Bring the project up on `dev-env`:
   ```bash
   cd /workspace/<project>
   docker-compose -f compose.yml up -d --build
   ```
   The compose must attach to `dev-env` as an external network
   (`networks: dev-env: { external: true, name: dev-crew-dev-env }`). Add it if missing.
3. Verify health — hit the project's health endpoint (e.g. `curl http://localhost:8080/healthz`
   or the service's `/healthz` on the network).
4. Exercise the change against the running service where possible (smoke the path you built).
5. Tear down or leave running — `dev-env` is a sandbox; break freely.

## Rules

- **Never deploy to `staging-env`** — that is devops's pre-prod gate. Ask devops for staging.
- Don't commit secrets; env vars come from the project's `.env` (gitignored).
- The image provides the `docker-compose` (standalone v2) binary. If it is missing,
  use plain `docker` commands or ask the manager to run compose from the host.
- Record the verification result (command + health output) in the PR description.
