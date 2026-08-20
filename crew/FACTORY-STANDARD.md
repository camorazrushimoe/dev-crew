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

## The workflow

1. **Spec** — manager + tech-pm write the OpenSpec spec.
2. **Adversarial review** — every involved agent reviews the spec from its own
   lens (product / engineering / infra / testability) and posts a comment on the
   spec's GitHub issue: a verdict (`approve` / `needs-changes`) + at most 3
   blocking findings. Evaluation, not redesign — no alternative implementations.
3. **Plan** — tech-pm decomposes the reviewed spec into an approved plan (Linear).
4. **Implement** — developer works in a `feature/<ticket>-slug` branch, opens a PR, does not merge.
5. **Review** — manager + qa review the PR against the spec.
6. **Merge** — only after review passes.
7. **Deploy** — devops deploys merged code to the dev/staging cluster and verifies.

## Roles

| Agent | Door | Owns |
|---|---|---|
| developer | 8651 | implements specs as code, opens PRs |
| qa | 8652 | verifies against specs, QA reports |
| tech-pm | 8653 | decomposes specs into plans/tickets |
| devops | 8654 | owns test/staging env, deploys merged code |

## Language

Work in English — code, commits, PRs, tickets and reports.
