# Design: adversarial review + full workflow

## Context

The factory had a planning gate but no explicit spec-review stage, no QA testing
stage, and no documented end-to-end workflow. This change adds the missing stages
and writes the whole pipeline down as the agents' shared contract.

## Stage position (full workflow)

```
spec → adversarial review (GitHub issue) → plan & decompose (tech-pm) →
implement (developer, feature branch, PR) → code review → merge →
deploy dev (devops) → QA testing (test plans, report, bugs→bus) →
QA approve → deploy staging (devops)
```

## Adversarial review

A single round before planning. Each agent reviews from its own lens:

| Agent | Lens | Focus |
|---|---|---|
| tech-pm | Product | value, priority, completeness, usability |
| developer | Engineering | simpler / more efficient / cheaper; ambiguity |
| devops | Infrastructure | new services/deps, deploy risks (else "N/A") |
| qa | Testability | how to test, Gherkin adequacy, untestable parts |

Bounded: verdict (`approve` / `needs-changes`) + at most 3 blocking findings;
non-blocking → backlog; **no redesign**. Posted as GitHub issue comments (one per
agent). No consolidation — the manager reads the reviews directly.

## Plan & decompose

After review, tech-pm writes the plan; if the work is too large, it is split into
smaller tickets (Linear) before dispatch. The manager decides.

## QA testing stage

- **Test plans** live in the project repo; qa updates and runs them after each merge.
- **Test report** recorded per release candidate (passed/failed/severity/verdict).
- **Bugs** published to the shared-memory bus (`bug.found` + debugging payload) and
  recorded durably (issue/ticket).
- **Release gate**: qa approves the build before staging.

## Release pipeline

Devops deploys merged code to `dev-env`; the same build is promoted to `staging-env`
only after QA approval.

## Escape hatch

The manager may override the workflow in a critical situation by explicit approval;
every override is recorded immediately as tech debt (GitHub issue labelled
`tech-debt` or a Linear ticket) so shortcuts are never silent.

## Goals / Non-Goals

**Goals**
- Catch bad ideas, complexity and untestable specs before planning.
- Give QA an explicit place (test plans, report, bugs, release gate).
- Document the full workflow as the agents' shared contract.
- Keep the review bounded (≤3 blocking, no redesign) so work still starts.

**Non-Goals**
- Iterative review loops or a consolidation agent (deferred).
- Defining test-plan formats / bug-report templates in detail (deferred).
- Replacing Linear for planning (out of scope for now).
