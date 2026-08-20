# Design: Adversarial review (spec review gate)

## Context

The planning gate decomposes a spec into a plan and reviews the plan. But the spec
itself is never challenged before planning, and devops joins only at deploy. The
goal of this change is a cheap, bounded adversarial review of the SPEC — before any
plan or code — so bad ideas and untestable requirements are caught early, without
paralysing the team with endless redesign suggestions.

## Stage position

```
новая спека → adversarial review (GitHub issue) → manager decides →
tech-pm writes plan → implement → verify → merge → deploy
```

The review is a single round: each agent posts one comment; the manager reads the
reviews and decides what to fold back into the spec. No consolidation step for now.

## Role lenses

| Agent | Lens | Focus |
|---|---|---|
| tech-pm | Product | value, priority, completeness, usability |
| developer | Engineering | simpler / more efficient / cheaper; ambiguity |
| devops | Infrastructure | new services/deps, deploy risks (else "N/A") |
| qa | Testability | how to test, Gherkin adequacy, untestable parts |

## Bounded-ness (why it stays cheap)

- Verdict required: `approve` / `needs-changes` (devops may add `N/A`).
- At most **3 blocking** findings per agent; everything else is non-blocking and
  goes to the backlog without blocking the work.
- **No redesign**: agents flag risks/gaps/ambiguities, they do not propose an
  alternative implementation. This is the key guard against analysis paralysis.
- One round, no consolidation — the manager decides.

## Location

GitHub issue (one per spec). Each agent posts its review as a separate comment.
No Linear ticket is required for the review (Linear may be dropped later).

## Goals / Non-Goals

**Goals**
- Catch bad ideas, complexity and untestable specs before planning.
- Keep the review bounded (≤3 blocking, no redesign) so work still starts.

**Non-Goals**
- Iterative review loops or a consolidation agent (deferred).
- Replacing Linear for planning (out of scope for now).
- Enforcing review on code PRs (that is the existing "review against the spec").
