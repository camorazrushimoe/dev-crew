# Skill Guardrails

## ADDED Requirements

### Requirement: Three skill path layers

The factory distinguishes three layers:

| Layer | Location | Mutability |
|---|---|---|
| **Factory skills (git)** | `agents/<role>/skills/` in the dev-crew repo | Change only via reviewed PR |
| **Factory skills (runtime mount)** | Read-only mount (e.g. `/opt/data/skills/dev-crew`) | Not writable by agents |
| **Runtime / personal notes** | Agent `hermes-home/` (gitignored), including any runtime skill drafts | Writable; not factory contract |

### Requirement: Factory skills are not writable at runtime

Agents SHALL NOT create or patch factory skills. Writes under the factory skill
git tree or the read-only skills mount SHALL be rejected by the environment
(read-only mount and/or runtime guard). There is no "force through PR" path from
inside a running agent — a human or manager opens a normal PR in the repo.

#### Scenario: write to factory skill mount is rejected

- **WHEN** an agent attempts to create or modify a file under the factory skills mount
- **THEN** the write SHALL fail (read-only filesystem or explicit guard)
- **AND** factory behaviour SHALL remain unchanged

#### Scenario: self-improvement cannot drift factory skills

- **WHEN** Hermes (or equivalent) self-improvement runs during a task
- **THEN** it SHALL NOT permanently alter factory skills under the git tree or RO mount

### Requirement: Runtime skill-like writes are visible

If an agent creates or patches skill-like files under `hermes-home/` (runtime
layer), the system SHOULD emit a bus event so the manager can see it:

- `skill.created` — payload includes path and short description
- `skill.patched` — payload includes path and a short diff or summary

These runtime files are **not** factory skills and do not change the shared
contract until promoted via a reviewed PR into `agents/<role>/skills/`.

#### Scenario: hermes-home skill draft is observable

- **WHEN** an agent writes a skill-like file under hermes-home
- **THEN** a `skill.created` or `skill.patched` bus action SHOULD be published when feasible
- **AND** the manager SHALL be able to inspect hermes-home without treating the draft as factory contract

### Requirement: Promotion path is a normal PR

Promoting a useful runtime skill into the factory SHALL be done by copying it into
`agents/<role>/skills/` on a feature branch and opening a PR — the same review
gate as any other foundation change.
