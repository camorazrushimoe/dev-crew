# Workspace — shared code area

This directory is bind-mounted into the agents as `/workspace`:

| Agent | Access | Use |
|-------|--------|-----|
| `developer` | read/write | clones project repos, works on feature branches |
| `qa` | read/write | checks out branches and runs the test suite |
| `devops` | read/write | brings up project compose files, deploys to environments |
| `tech-pm` | read-only | reads code for planning/review |

## How projects live here

Each project gets its own subdirectory (typically a git clone):

```
workspace/
  community-intelligence/     # project repo (cloned)
  some-other-project/         # another repo
```

## Conventions

- The workspace itself is **runtime data** — everything except this `README.md`
  is gitignored (see the repo `.gitignore`).
- Agents use their **own git identity** (`agents/<name>/hermes-home/.gitconfig`)
  and follow the feature-branch + PR flow; they never commit directly to `main`.
- Project services (databases, apps) are **not** part of the foundation — each
  project declares them in its own `workspace/<project>/compose.yml` and attaches
  to the `dev-env` / `staging-env` networks via `external: true`.
