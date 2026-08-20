# Tasks: developer-owned dev cluster

## 1. Spec

- [ ] 1.1 Update `openspec/specs/environments/spec.md` — add "Developer owns the dev-env sandbox"; scope devops to `staging-env`; update onboarding + stage-progression scenarios.
- [ ] 1.2 Update `openspec/specs/agent-roles/spec.md` — "Owns" column (developer: implement + dev-env; devops: staging-env).

## 2. Agent contracts (SOUL)

- [ ] 2.1 `developer` SOUL — may `docker compose up` on `dev-env`; verify before PR; never touch `staging-env`.
- [ ] 2.2 `devops` SOUL — owns `staging-env` (pre-prod); no longer "only deployer" of dev-env.
- [ ] 2.3 `qa` SOUL — verifies release candidates on `staging-env`.

## 3. Skills

- [ ] 3.1 New `agents/developer/skills/deploy-dev/SKILL.md` — how to bring the project up on `dev-env` (compose, health, teardown).
- [ ] 3.2 Update `agents/devops/skills/environment/SKILL.md` and `deploy/SKILL.md` — scope to `staging-env`.

## 4. Docs

- [ ] 4.1 Update `crew/FACTORY-STANDARD.md` — new pipeline (dev-env pre-PR, staging gate).
- [ ] 4.2 Update `README.md` — environment ownership + workflow.

## 5. Runtime wiring (after spec approval)

- [ ] 5.1 Mount `/var/run/docker.sock` into the `developer` container (and keep devops's).
- [ ] 5.2 Add the compose plugin to `developer` and `devops` (custom image `FROM nousresearch/hermes-agent:latest` + docker-compose-plugin, or boot-time install).
- [ ] 5.3 Recreate the `developer` and `devops` containers.
- [ ] 5.4 Verify: `developer` can `docker compose up` a project on `dev-env` and see a healthy service.

## 6. End-to-end check

- [ ] 6.1 Run one slice (e.g. SpacedBro BON-27) through the new pipeline: dev verifies on `dev-env` → PR → merge → devops deploys `staging-env` → QA verifies.
