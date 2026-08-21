# Tasks: developer-owned dev cluster

## 1. Spec

- [x] 1.1 Update `openspec/specs/environments/spec.md` — add "Developer owns the dev-env sandbox"; scope devops to `staging-env`; update onboarding + stage-progression scenarios.
- [x] 1.2 Update `openspec/specs/agent-roles/spec.md` — "Owns" column (developer: implement + dev-env; devops: staging-env).
- [x] 1.3 Update `openspec/specs/qa-testing/spec.md` — QA verifies on `staging-env`; release gate flipped (approve after staging deploy, not before).

## 2. Agent contracts (SOUL)

- [x] 2.1 `developer` SOUL — may `docker compose up` on `dev-env`; verify before PR; never touch `staging-env`.
- [x] 2.2 `devops` SOUL — owns `staging-env` (pre-prod); no longer "only deployer" of dev-env.
- [x] 2.3 `qa` SOUL — verifies release candidates on `staging-env`.

## 3. Skills

- [x] 3.1 New `agents/developer/skills/deploy-dev/SKILL.md` — how to bring the project up on `dev-env` (compose, health, teardown).
- [x] 3.2 Update `agents/devops/skills/environment/SKILL.md` and `deploy/SKILL.md` — scope to `staging-env`.

## 4. Docs

- [x] 4.1 Update `crew/FACTORY-STANDARD.md` — new pipeline (dev-env pre-PR, staging gate).
- [x] 4.2 Update `README.md` — environment ownership + workflow.

## 5. Runtime wiring (after spec approval)

- [x] 5.1 Mount `/var/run/docker.sock` into the `developer` container (and keep devops's).
- [x] 5.2 Add the compose binary to `developer` and `devops` (thin image `Dockerfile.agent` = `FROM nousresearch/hermes-agent:latest` + `docker-compose` apt package).
- [x] 5.3 Recreate the `developer` and `devops` containers.
- [x] 5.4 Verify: `developer` has `docker-compose` + host daemon access via the socket (can reach `dev-crew-dev-env`).

## 6. End-to-end check

- [ ] 6.1 Run one slice (e.g. SpacedBro BON-27) through the new pipeline: dev verifies on `dev-env` → PR → merge → devops deploys `staging-env` → QA verifies.
