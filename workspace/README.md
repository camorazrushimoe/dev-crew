# Workspace — team tooling/env mount

This directory is bind-mounted into the agents as `/workspace`. It is **not** the
project work clone: agents do **not** clone project repos here and do **not** keep
feature branches here. Project code lives in **private clones under each agent's
hermes-home** (`/opt/data/workspace/<project>/`), and **GitHub is the shared
medium** — pull requests, not shared working trees.

`/workspace` holds the project's **services / tooling / environment**: the compose
files and data that make a project runnable on the dev/staging networks.

| Agent | Access | Use |
|-------|--------|-----|
| `developer` | read/write | brings up project services on `dev-env` for its sandbox work |
| `qa` | read/write | brings up project services to verify against the approved plan |
| `devops` | read/write | brings up project compose files, deploys to environments |
| `tech-pm` | read-only | inspects the environment for planning/review |

## How projects attach here

Each project keeps its environment pieces under its own subdirectory:

```
workspace/
  community-intelligence/     # project services/compose/tooling
  some-other-project/         # another project's env
```

Project work (code, reviews, branches) does **not** live here — see the private
clones under each agent's hermes-home instead.

## Conventions

- The workspace itself is **runtime data** — everything except this `README.md`
  is gitignored (see the repo `.gitignore`).
- Project code changes flow through private hermes-home clones → feature branch →
  PR → merge on GitHub; never through a shared workspace tree.
- Agents use their **own git identity** (`agents/<name>/hermes-home/.gitconfig`)
  in their private clones.
- Project services (databases, apps) are **not** part of the foundation — each
  project declares them in its own `workspace/<project>/compose.yml` and attaches
  to the `dev-env` / `staging-env` networks via `external: true`.
