# Tasks: Review-cycle loop breaker

Implementation checklist for the PR that follows this spec (Batch A).
Order matters; each step keeps the test suite green.

## Code — `dashboard/pipeline_driver.py`

- [ ] **D3 gap first:** add the missing stage transition so a *new*
      `needs-changes` verdict after a re-review advances the round instead of
      stalling. Resolve the stale-vs-new verdict ambiguity deterministically
      (recommended: per-reviewer verdict-comment counters in state, recorded at
      each review/re-review dispatch).
- [ ] Add per-PR `rounds` counter; increment when a fix is dispatched (both
      reviewers `needs-changes` on the same head → one round, one fix).
- [ ] Cap check before fix dispatch: if `rounds >= DRIVER_MAX_REVIEW_ROUNDS`
      and the latest verdict is `needs-changes`, return the `needs-human`
      action instead of `fix`.
- [ ] `needs-human` action:
      - post PR comment: first line `<!-- conveyor:needs-human -->`, header
        `## Loop breaker`, body with ticket + rounds + no verdict lexemes and
        no reviewer header tokens (see design D4);
      - set `needs_human: true`, `needs_human_at`, `reason` in state;
      - if the PR is ticket-bound, dispatch the needs-human task to tech-pm
        (crew-send, `Ticket <ID>` binding; instruction: move Linear ticket to
        needs-human/Blocked state + comment starting `Needs human:`, do not
        dispatch further work);
      - never dispatch fix / re-review / merge for a `needs_human` PR.
- [ ] Add `DRIVER_MAX_REVIEW_ROUNDS` env (default `2`, minimum 1) + wire into
      module constants; document in the module docstring and `--help`-style
      usage header.
- [ ] Make the verdict parser ignore the driver's own comment
      (`_verdict` / `_reviewer` short-circuit on the `<!-- conveyor -->`
      sentinel) so the needs-human comment cannot flip parsed verdicts.
- [ ] Keep idempotency + best-effort semantics; state saved once per run when
      anything acted; `DRIVER_DRY_RUN` previews needs-human actions.
- [ ] Backward compatibility: state entries without `rounds` / `needs_human`
      behave as `0` / `false`.

## Tests — `tests/test_pipeline_driver.py`

- [ ] Cap reached → `needs-human` (no `fix`) on the third `needs-changes`
      verdict with default cap 2.
- [ ] `DRIVER_MAX_REVIEW_ROUNDS=1` → second `needs-changes` escalates.
- [ ] Both reviewers `needs-changes` on the same head → one fix (one round).
- [ ] `needs_human` terminal suppresses fix / re-review / merge, even with new
      head commits and `approve` verdicts present.
- [ ] State cleared (human reset) → driver resumes.
- [ ] Needs-human comment body parses to no verdict and no reviewer.
- [ ] Legacy state (no new keys) behaves as 0 / false.
- [ ] Re-review returns `needs-changes` → round advances (fix or needs-human at
      cap); no double-dispatch while a re-review is in flight (reconciles
      `test_rereview_waiting_does_not_refix`).

## Spec promotion (merge this change into the capability)

- [ ] When the base `pipeline-dispatch` capability spec is promoted to
      `openspec/specs/pipeline-dispatch/spec.md`, merge this change's
      requirements (delta in `specs/pipeline-dispatch/spec.md`) into it and
      archive `openspec/changes/review-cycle-loop-breaker/`.
- [ ] Update the driver usage docs (module docstring / README dashboard
      section if the conveyor is documented there) to mention the cap env var
      and the needs-human state.

## Verification

- [ ] `python3 -m unittest tests.test_pipeline_driver -v` green.
- [ ] Dry-run trace: simulate the D3 trace (2 rounds + third verdict) in a
      scratch state file with `DRIVER_DRY_RUN=1` and confirm the needs-human
      actions print and no fix/merge is dispatched.
