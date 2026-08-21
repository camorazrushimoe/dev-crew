# Design: factory ops hardening

## Context

The first end-to-end SpacedBro MVP run showed that the foundation is runnable but
not yet operable without constant manual stitching. Five concrete gaps are closed
by this change at the **spec level**; implementation follows after review.

## Priority after merge

1. Policy: Projects (#13), hygiene (#14), skill guardrails (#15)
2. Runtime: completion hooks (#12)
3. UI: run-supervision (#16)

## 1. Deterministic task-completion hooks (#12)

### Problem
`crew-send.py` returns 202 only. "Report when done" lives in SOUL.md (LLM
discretion). Manager polls Linear / GitHub / logs.

### Approach
**Preferred mechanism:** thin wrapper around the door handler (knows the inbound
message and can observe turn end). Hermes hook is acceptable if it can see the
same binding data.

| Event | Effect |
|---|---|
| **START** | Bus `task.started`; optional Linear In Progress + short comment |
| **FINISH** | Bus `task.finished`; best-effort Linear comment + state move; best-effort manager webhook |
| **STALE** | Bus `task.stale` if silent > N minutes (default ~30) on an assigned task |

**Ticket binding:** dispatch messages MUST include `Ticket <ID>` (see task-dispatch).
Runtime parses that id. If missing: bus event still fires, no Linear state move.

**State rules:** success + PR/reviewable artifact → In Review; success otherwise →
Done; failure/blocked → Blocked. Payload `status` comes from turn outcome, not
free-form prose alone.

**Failure mode:** Linear/webhook errors are logged; agent process must not crash
or hang. Bus publish is the durable minimum signal.

Payload (structured):
```json
{
  "agent": "developer",
  "ticket": "BON-27",
  "status": "success|failure|blocked",
  "summary": "one line",
  "run": "SpacedBro MVP"
}
```

## 2. Linear Projects as grouping unit (#13)

### Problem
Skills teach "epic = parent ticket + children". Linear Projects are first-class.

### Approach
- A product effort **is** a Linear Project (create or reuse).
- tech-pm links every ticket via `projectId`.
- No artificial parent epic solely for grouping.
- Update `linear-workflow`, `to-tickets`, `task-dispatch`, FACTORY-STANDARD,
  planning-gate.

## 3. Workspace hygiene (#14)

### Problem
Agents left review drafts in `workspace/<project>/`.

### Approach
- Scratch = non-deliverable files (review drafts, temp notes, dumps, swap files).
- Scratch only in `$HERMES_HOME` or `/tmp`.
- Explicit `git add` paths; no `git add -A`.
- Rule in FACTORY-STANDARD + every SOUL.md.

## 4. Skill guardrails (#15)

### Problem
Self-improvement drifted a gitignored runtime skill and biased reviews (#9/#10).

### Approach — single MUST path
Three layers:
1. Git factory skills (`agents/<role>/skills/`) — PR only
2. RO mount at runtime — writes fail
3. hermes-home runtime drafts — allowed, not contract; SHOULD emit bus events

No in-agent "open a PR for me" path. Promotion = human/manager normal PR.

## 5. Run-supervision view (#16)

### Problem
Health dashboard only; manager still stitches Linear + GitHub + logs.

### Approach
Run = Linear Project. Show tickets, agents, cost-when-available.
Missing cost must not break the page.
Linear/GitHub tokens: instance config only, read-only scope preferred.

## Goals / Non-Goals

**Goals**
- Manager gets a push (or at least a bus event) when any agent finishes.
- Product efforts are Linear Projects, not synthetic epics.
- Workspace stays clean after a full run.
- Factory skills cannot drift outside review.
- One page answers "what is the factory doing for this run?".

**Non-Goals (this change)**
- Full implementation of the door wrapper/hook or dashboard UI (spec first).
- Replacing Linear entirely.
- Building a full token-accounting subsystem.
- Changing product-repo OpenSpec processes.
