# Change: Developer owns the dev cluster (dev-env as a real sandbox)

## Why

Today the `developer` agent writes code but **cannot actually run it in a container**
before opening a PR: it has the Docker CLI (`docker 26.1.5`) but no `docker.sock`
mount and no compose plugin. During the SpacedBro MVP run (BON-27 scaffold, PR #5),
the developer had to validate its work via `pytest` + direct runtime steps and flag:
*"I could not run `docker compose up` (no Docker daemon in the dev container)"*.

At the same time the factory contradicts itself: the `environment` skill describes
`dev-env` as *"developer builds and breaks freely"*, but the devops SOUL says *"I am
the ONLY agent who deploys"*. The intent and the wiring disagree.

We want a clean model:

- **`dev-env` = the developer's sandbox ("Dev Cluster").** The developer can
  `docker compose up`, test, iterate and break freely there — like its own local
  Docker — BEFORE opening a PR.
- **`staging-env` = the pre-prod gate.** Only devops deploys there (merged, reviewed
  code), and QA verifies release candidates on staging.

This also **simplifies the pipeline**: today devops deploys twice (dev → QA → staging);
after this change the developer self-serves on dev-env pre-PR, and the only formal
gate is merge → devops deploy staging → QA test → approve.

## What Changes

- `dev-env` becomes developer-owned (sandbox); `staging-env` becomes the devops-owned
  pre-prod gate.
- The developer gets the tooling to use `dev-env`: Docker daemon access + the compose
  plugin (devops also gets the compose plugin, which it lacks today).
- Role contracts, skills and docs are updated to match (see Impact).

## Impact

- `openspec/specs/environments/spec.md` — redefine environment ownership.
- `openspec/specs/agent-roles/spec.md` — update the "Owns" column.
- `agents/developer/hermes-home/SOUL.md` — developer may deploy to `dev-env`.
- `agents/devops/hermes-home/SOUL.md` — devops owns `staging-env` (no longer "only deployer").
- `agents/qa/hermes-home/SOUL.md` — QA verifies release candidates on `staging-env`.
- `agents/developer/skills/deploy-dev/` (new) — how to run the project on `dev-env`.
- `agents/devops/skills/{environment,deploy}/` — scoped to `staging-env`.
- `crew/FACTORY-STANDARD.md`, `README.md` — updated pipeline.
- `docker-compose.yml` — mount `docker.sock` into `developer`; add the compose plugin
  to `developer` and `devops` (see tasks; implemented after this spec is approved).

## Non-goals (deferred)

- True per-environment Docker daemons (DinD) — deferred. A shared host daemon with
  network-based separation (`dev-env` / `staging-env` networks) is sufficient for the
  single-host factory.
- Hard security isolation between dev and staging — separation is by convention
  (network naming + SOUL rules) for now; a socket proxy or DinD can harden later.
