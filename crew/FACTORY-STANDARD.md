# Dev Crew — Factory Standard

This factory builds software **spec-first**: every task is backed by an OpenSpec
spec. If there is no spec, there is no work.

## The golden rule

**No spec → no work.** When a task arrives without a reference to a spec, do NOT
start coding, testing or planning the implementation. Ask: **"Where is the spec?
Who wrote it?"** The manager or tech-pm must point you to the spec before you begin.

## What a spec looks like

A project's spec lives in its repo under `openspec/`:

- `openspec/specs/<capability>/spec.md` — requirements + WHEN/THEN scenarios (the contract).
- `openspec/changes/<change>/proposal.md` — why + what changes.
- `openspec/changes/<change>/design.md` — technical approach.
- `openspec/changes/<change>/tasks.md` — implementation checklist.

## The workflow (end to end)

1. **Spec** — manager + tech-pm write the OpenSpec spec.
2. **Adversarial review** — every involved agent reviews the spec from its own
   lens (product / engineering / infra / testability) and posts a comment on the
   spec's GitHub issue: a verdict (`approve` / `needs-changes`) + at most 3
   blocking findings. Evaluation, not redesign.
3. **Plan & decompose** — tech-pm turns the reviewed spec into a plan and a Linear
   **Project** (the grouping unit). Large work is split into smaller tickets linked
   to that Project. The manager decides.
4. **Implement** — developer implements a piece on a `feature/<ticket>-slug`
   branch, opens a PR, and waits for review (does not self-merge).
5. **Code review** — qa + manager review the PR against the spec.
6. **Merge** — only after review passes.
7. **Deploy to dev** — devops deploys the merged code to `dev-env` (first test cluster).
8. **QA testing** — qa updates the test plans, runs tests, and records a test
   report. Bugs are published to the shared-memory bus (`bug.found` + debugging
   info) and recorded durably.
9. **QA approve** — qa approves the build and signals devops.
10. **Deploy to staging** — devops deploys the approved build to `staging-env`.

## Linear Projects (not synthetic epics)

A product effort **is** a Linear Project. tech-pm creates the Project and links
every ticket to it. Do not invent a parent "epic" ticket solely for grouping.
Tickets may still declare blocking edges between each other; the Project is the
filter and progress view.

## Task completion (deterministic)

Task start/finish is signalled by the **runtime** (completion hooks), not only by
LLM comments. On finish the factory auto-comments Linear, updates ticket state,
pings the manager, and publishes `task.finished` on the bus. Agents should still
comment useful detail, but the manager-facing signal MUST NOT depend on prompt
discipline alone.

## Workspace hygiene

- Write drafts, scratch notes and temp files only under `$HERMES_HOME` or `/tmp`.
- Never leave non-intentional files under `workspace/<project>/`.
- Before opening a PR, clean untracked scratch from the project tree.
- Never `git add -A` blindly — stage explicit paths.

## Skill guardrails

Factory skills under `agents/<role>/skills/` change only via reviewed PR. Do not
silently create or patch those skills at runtime. Runtime/personal notes may live
under hermes-home (gitignored). Skill create/patch events should be visible on
the bus (`skill.created` / `skill.patched`).

## Escape hatch (critical override)

In a critical situation the manager MAY override the workflow (skip review, deploy
directly, etc.) by explicitly approving the override. Every override SHALL be
recorded immediately as **tech debt** — a GitHub issue labelled `tech-debt` (or a
Linear ticket) — so the shortcut is never silent.

## Roles

| Agent | Door | Owns |
|---|---|---|
| developer | 8651 | implements specs as code, opens PRs |
| qa | 8652 | verifies against specs, test plans + reports, approves releases |
| tech-pm | 8653 | decomposes specs into plans/tickets under Linear Projects |
| devops | 8654 | owns test/staging env, deploys merged code |

## Language

Work in English — code, commits, PRs, tickets and reports.
