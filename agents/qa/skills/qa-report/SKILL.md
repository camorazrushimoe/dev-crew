---
name: qa-report
description: Write a structured QA report after testing. Use when reporting test results, bug findings, or giving a merge verdict on a PR.
---

# QA Report

After verifying a change, produce a report with this structure (in English):

```
## QA Report — <ticket>

**Scope**: what was tested (ticket + brief).
**Result**: PASS / FAIL / NEEDS CHANGES.
**Tests run**: list of test commands + outcomes.
**Bugs found**:
- [severity] description + steps to reproduce + expected vs actual.
**Coverage gaps**: areas not tested and why.
**Verdict**: ready to merge / needs changes (list required fixes).
```

## Rules

- Severity: `blocker` (must fix), `major`, `minor`, `nits`.
- Every bug gets reproducible steps.
- Post the report to Linear (comment on the ticket) and to the bus.
- Be specific and factual — no vague "looks fine".
