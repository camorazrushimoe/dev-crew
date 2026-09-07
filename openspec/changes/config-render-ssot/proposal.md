# Proposal: Instance configs render from the SSOT — closeout of #40

## Why

Issue #40 (2026-08-28): the standalone dev-crew agents pinned their LLM provider
by hand and were **not** derived from the Office single source of truth
(`agent-office/tokens/tokens.yaml`). When the factory migrated to DeepSeek, the
crew kept pointing at the dead runinfra endpoint (`qwen3-8-27b`,
`https://api.runinfra.ai/v1`). Every agent came up, `docker compose up` and
`docker ps` looked healthy, and the 403 only surfaced on the first real LLM
call — mid-task.

The root failure is already fixed on main:

- **#37** — `agents/<role>/hermes-home/config.yaml` became `config.yaml.template`
  and both composes render it at container start (`crew/render_config.py`)
  instead of hand-maintaining configs.
- **#45** — templates and the default compose point at
  `deepseek-v4-flash` / `https://api.deepseek.com/v1`.

What never happened: an end-to-end verification of render-from-SSOT on a
composed instance, a bring-up smoke step in the template docs (bring-up still
declares success on a green `docker ps`), and cleanup of the stale provider text
that let the rot re-enter silently. This change closes #40 as verified and
documented.

## What changes

1. **Render-from-SSOT is verified end-to-end on a composed instance.** On the
   live `dev-1` instance the agents' configs are rendered by the Office overlay
   (`office/render_config.py`) from `tokens/tokens.yaml`: identity resolved via
   `FACTORY_NAME` / `TEAM_NAME` / `AGENT_ID`, `llm.base_url` + the factory key
   (`llm.factories.dev-crew`) substituted into `config.yaml.template`, and the
   resulting `$HERMES_HOME/.env` header-marked *"Secrets come from the single
   source of truth: tokens/tokens.yaml"*. Every agent answers an LLM round-trip.
   Evidence is recorded in `design.md`.

2. **Bring-up smoke check in the template docs.** The bring-up section of the
   template docs SHALL end with an explicit per-agent LLM round-trip
   (`docker exec dev-crew-<role> hermes chat -q "Reply with exactly: OK"`) that
   fails loudly, and SHALL reference the Office overlay's `scripts/smoke.py` for
   office-composed instances. A green `docker ps` alone is never "up" — that is
   exactly the check that would have caught the 403 before dispatch.

3. **Stale references cleaned.** The LLM key is named inconsistently across the
   template family — `.env.example` still says *"LLM (runinfra, one key shared
   by all agents)"* and declares `CUSTOM_API_KEY`, the templates reference
   `${DEEPSEEK_API_KEY}`, the default compose passes `DEEPSEEK_API_KEY`, and the
   standalone compose still passes `CUSTOM_API_KEY`. Docs and config-template
   comments are aligned (decision D3 in `design.md`), and any text implying keys
   are duplicated per agent in `.env`, or that the template composes read
   `tokens/tokens.yaml` directly, is corrected: template composes source the
   instance `.env`; the strict `tokens.yaml` SSOT exists via the Office overlay
   on live composed instances.

## Acceptance criteria

- A composed instance (Office overlay path) boots agents whose
  `/opt/data/config.yaml` is fully rendered (no literal `${VAR}`), whose
  `/opt/data/.env` carries the SSOT header, and each agent answers an LLM
  round-trip with exactly `OK`.
- Template bring-up docs end with the smoke step and state how to run it in both
  modes (standalone inline round-trip; office-composed `scripts/smoke.py`); no
  passage declares the factory up on `docker ps` alone.
- `grep -riE 'runinfra|qwen'` matches nothing in the repo; the LLM env key is
  named consistently across `.env.example`, both composes and all four
  `config.yaml.template` files; no doc claims per-agent `.env` key duplication
  or direct `tokens.yaml` reads by the template composes.

## Impact

- `openspec/changes/config-render-ssot/` — this change (proposal, design, tasks,
  `layer-separation` spec delta).
- Closeout implementation PR (after this spec merges): `.env.example`,
  `README.md`, `docs/architecture.md`, `docs/office-template.md`,
  `docker-compose.yml`, `docker-compose.standalone.yml` — see `tasks.md`.

## Out of scope

- Runtime changes to the render path (already on main via #37 / #45).
- Adopting the Office overlay into the template composes: the template keeps
  sourcing the instance `.env`; strict `tokens.yaml` SSOT remains an Office
  overlay property of live composed instances. This boundary is documented, not
  moved.
- Issue #40's optional dashboard "LLM reachable" indicator (backlog).
