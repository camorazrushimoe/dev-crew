# Skill Guardrails

## ADDED Requirements

### Requirement: Factory skills change only via review

Skills under `agents/<role>/skills/` (the tracked, factory-defining skills)
SHALL change only through a reviewable PR. Agents SHALL NOT silently create or
patch those skills at runtime.

#### Scenario: unsupervised skill write is blocked or reviewed

- **WHEN** an agent attempts to create or modify a skill under `agents/<role>/skills/`
- **THEN** the change SHALL either be rejected by the runtime
- **OR** SHALL be forced through a path that produces a reviewable PR

### Requirement: Self-improvement is scoped away from factory skills

Hermes (or equivalent) self-improvement features SHALL be disabled or scoped so
they cannot write under the tracked factory skill paths without review.

#### Scenario: self-improvement does not drift factory behaviour

- **WHEN** self-improvement runs during a task
- **THEN** it SHALL NOT permanently alter factory skills outside a reviewed change

### Requirement: Skill mutations are visible

If a skill is created or patched (including under hermes-home runtime areas),
the system SHALL emit a bus event so the manager can see it:

- `skill.created` — payload includes path and short description
- `skill.patched` — payload includes path and a short diff or summary

#### Scenario: skill patch is not silent

- **WHEN** a skill file is created or patched
- **THEN** a corresponding bus action SHALL be published
- **AND** the manager SHALL be able to observe the event without inspecting container filesystems

### Requirement: Personal runtime notes are separate

Agents MAY keep personal/runtime notes under `hermes-home/` (gitignored). Those
are not factory skills and are not subject to the PR gate, but skill-like writes
that affect shared behaviour still SHOULD surface as bus events when feasible.
