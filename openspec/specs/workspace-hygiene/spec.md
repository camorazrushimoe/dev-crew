# Workspace Hygiene

## ADDED Requirements

### Requirement: Scratch stays out of the project tree

Agents SHALL write drafts, scratch notes, review drafts and temporary files only
under their own `$HERMES_HOME` (hermes-home) or `/tmp`. They SHALL NOT write
scratch under `workspace/<project>/`.

**Scratch** means any file that is not intentional project source, tests, config,
or docs that the agent intends to commit as part of the ticket. Examples of
scratch: review drafts (`*-review*.md`), temp notes, downloaded dumps, editor
swap files, ad-hoc scripts not part of the deliverable.

#### Scenario: review draft is not left in the project repo

- **WHEN** an agent produces a scratch review or draft during a run
- **THEN** the file SHALL live under hermes-home or `/tmp`
- **AND** SHALL NOT appear as an untracked file in `workspace/<project>/`

### Requirement: Clean tree before PR

Before opening a PR, the agent SHALL ensure the project working tree contains
only intentional, staged changes (plus gitignored build artifacts). Untracked
scratch SHALL be removed or moved out of the project tree.

#### Scenario: PR is opened from a clean tree

- **WHEN** an agent opens a PR for project work
- **THEN** `git status` in the project SHALL not show agent-generated scratch files

### Requirement: No blind git add

Agents SHALL NOT run `git add -A` (or equivalent) on a project workspace. Staging
SHALL be explicit (named paths).

#### Scenario: only intended paths are staged

- **WHEN** an agent stages changes for a commit
- **THEN** it SHALL stage specific paths
- **AND** SHALL NOT use a blanket add of the entire tree

### Requirement: Rule is documented in FACTORY-STANDARD and SOUL.md

The scratch rule SHALL be stated in `crew/FACTORY-STANDARD.md` and in each
agent's `SOUL.md`.

#### Scenario: factory standard states the rule

- **WHEN** a reader opens `crew/FACTORY-STANDARD.md`
- **THEN** the document SHALL describe the allowed locations for scratch files

#### Scenario: each agent SOUL states the rule

- **WHEN** a reader opens any agent `SOUL.md`
- **THEN** the document SHALL state that scratch goes to hermes-home or `/tmp`, not `workspace/`
