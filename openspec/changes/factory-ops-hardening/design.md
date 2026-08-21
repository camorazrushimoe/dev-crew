# Design: factory ops hardening

## Context

The first end-to-end SpacedBro MVP run showed that the foundation is runnable but
not yet operable without constant manual stitching. Five concrete gaps are closed
by this change at the **spec level**; implementation follows after review.

## 1. Deterministic task-completion hooks (#12)

### Problem
`crew-send.py` returns 202 only. "Report when done" lives in SOUL.md (LLM
discretion). Manager polls Linear / GitHub / logs.

### Approach
Runtime Hermes hook (or thin wrapper around the door handler), **not** a prompt:

| Event | Effect |
|---|---|
| **START** | Optional: move Linear ticket → In Progress; short comment; bus `task.started` |
| **FINISH** (success or failure) | Auto-comment Linear (result + one-line summary); move state (Done / In Review / Blocked); webhook ping to manager; bus `task.finished` |
| **STALE** | If silent > N minutes on an assigned task → bus `task.stale` + optional Linear comment |

Payload (structured, not free text):
```json
{
  "agent": "developer",
  "ticket": "BON-27",
  "status": "success|failure|blocked",
  "summary": "one line",
  "run": "SpacedBro MVP"
}
```

The hook fires even if the agent skips its own final message. No change to agent
behaviour is required for the signal to exist.

## 2. Linear Projects as grouping unit (#13)

### Problem
Skills teach "epic = parent ticket + children". Linear Projects are first-class
(filter, board, progress) and already used informally ("SpacedBro MVP" project).

### Approach
- A product effort **is** a Linear Project.
- tech-pm creates the Project and links every ticket via `issueUpdate(input: { projectId })`.
- No artificial parent "epic" ticket is required; a goal/summary can live on the
  project description or a tracking comment.
- Update `linear-workflow`, `to-tickets`, `task-dispatch`, FACTORY-STANDARD,
  planning-gate.

## 3. Workspace hygiene (#14)

### Problem
QA (and others) wrote scratch review drafts into `workspace/spaced-bro/`, leaving
untracked files next to the real project content.

### Approach
Hard rule in FACTORY-STANDARD + every SOUL.md:

- Scratch / drafts / temp files → `$HERMES_HOME` (hermes-home) or `/tmp` only.
- Never write non-intentional files under `workspace/<project>/`.
- Before opening a PR: clean untracked scratch from the project tree.
- Never `git add -A` blindly; stage explicitly.

## 4. Skill guardrails (#15)

### Problem
Hermes "self-improvement" can create/patch skills under `agents/*/skills/` at
runtime. A gitignored drifted `spec-review` skill caused the Postgres bug.

### Approach
- Factory-defining skills under `agents/<role>/skills/` are **version-controlled**
  and change only via PR (like any other code).
- Runtime self-improvement is disabled or scoped away from those paths.
- Any skill create/patch that does occur SHALL emit a bus event
  (`skill.created` / `skill.patched`) with a short diff so the manager sees it.
- Agents MAY keep personal/runtime notes under `hermes-home/` (gitignored);
  those are not factory skills.

## 5. Run-supervision view (#16)

### Problem
Dashboard shows only agent health/state. Supervising a real run still requires
manual Linear + GitHub + log stitching.

### Approach
Extend the dashboard (or add a reporting surface) so one page shows a **run**:

- **run** = a Linear Project
- per ticket: state, linked PR (if any), assigned agent
- per agent: current task, state (idle/working), last activity
- **cost**: token usage per agent/ticket (from Hermes logs / state)

Data sources already exist (Linear GraphQL, GitHub API, Redis status keys,
agent logs). First version can be read-only aggregation; push-driven updates can
follow once completion hooks land.

## Goals / Non-Goals

**Goals**
- Manager gets a push when any agent finishes a dispatched task.
- Product efforts are Linear Projects, not synthetic epics.
- Workspace stays clean after a full run.
- Factory skills cannot drift outside review.
- One page answers "what is the factory doing right now for this run?".

**Non-Goals (this change)**
- Full implementation of the Hermes hook or dashboard UI (spec first).
- Replacing Linear entirely.
- Token-cost accounting infrastructure beyond what logs already expose.
- Changing product-repo OpenSpec processes.
