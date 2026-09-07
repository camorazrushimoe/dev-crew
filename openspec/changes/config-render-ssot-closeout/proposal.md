# Proposal: Config render from tokens.yaml SSOT — verify + closeout

## Why

Issue #40 exposed a **silent provider-rot failure mode**: the standalone factory's
agents pinned their LLM provider by hand (`config.yaml`, not derived from the
Office single source of truth), so when the factory-wide provider migrated to
DeepSeek the crew kept pointing at the dead runinfra endpoint. `docker compose
up` + `docker ps` looked healthy; the 403 only appeared on the first real LLM
call — mid-task.

The root failure is **already fixed on main**:

- **#37** — every agent now ships `agents/<role>/hermes-home/config.yaml.template`
  and renders it at container start (`crew/render_config.py` runs in the
  container command in **both** composes). Rendered `config.yaml` is gitignored.
- **#45** — templates and the default compose point at
  `deepseek-v4-flash` @ `https://api.deepseek.com/v1` with `${DEEPSEEK_API_KEY}`.

What remains is the **closeout** (approved plan, 2026-09-07): verify the render
path end-to-end on a composed instance, add the bring-up smoke check to the
template docs, and clean the stale references that still document the dead
runinfra/per-agent-`.env` model.

## Current state on main (verified 2026-09-07, `f404cbb`)

| Area | State | Stale? |
|---|---|---|
| `agents/*/hermes-home/config.yaml.template` (4) | `deepseek-v4-flash` @ `api.deepseek.com`, `api_key: ${DEEPSEEK_API_KEY}` | no |
| `docker-compose.yml` (Office-attached default) | passes `DEEPSEEK_API_KEY` per agent | no (comment on line 21 stale: names `${CUSTOM_API_KEY}`) |
| `docker-compose.standalone.yml` | passes `CUSTOM_API_KEY=${CUSTOM_API_KEY:-}` (×4) + stale comment | **yes** — templates now need `${DEEPSEEK_API_KEY}`; a standalone boot renders a literal `${DEEPSEEK_API_KEY}` placeholder |
| `.env.example` | LLM section: "runinfra", `CUSTOM_API_KEY=` | **yes** — no `DEEPSEEK_API_KEY` documented at all |
| `crew/render_config.py` docstring | names `${CUSTOM_API_KEY}` | yes (comment only) |
| `docs/office-template.md` | env-var list includes `CUSTOM_API_KEY` | yes |
| `docs/architecture.md` | Contract 3 + instance-config table: "tokens/tokens.yaml mounted read-only **per agent**" | **yes** — per-agent tokens model retired; template composes read `.env`, office overlay resolves identity from a single `tokens.yaml` SSOT |
| `tokens/tokens.example.yaml` | per-agent `agents: <role>: github/llm` sections | **yes** — duplicated per-agent key model (the "per-agent .env duplication" from the issue) |
| Template bring-up docs | README quick start: ad-hoc single ping `docker exec dev-crew-developer hermes chat -q "hello"` | yes — no smoke check; office has `scripts/smoke.py` |

## What

This change is **verify + closeout**, not a re-fix:

1. **Verify render-from-SSOT end-to-end for a composed instance** (acceptance
   criteria below). Note the documented nuance: the template composes source
   keys from the instance `.env`; the strict `tokens.yaml` SSOT flow exists via
   the office overlay used on live instances (office-lib `render_config.py` +
   `TOKENS_FILE`). Both paths must be exercised and the evidence recorded on
   issue #40.
2. **Bring-up smoke check in the template docs** — port the office
   `scripts/smoke.py` pattern into the template's bring-up documentation so a
   green `docker ps` is no longer treated as "factory up": the procedure ends
   with a per-agent LLM ping that fails loudly. Docs-only.
3. **Clean stale references** in docs/templates that still name
   runinfra/qwen/`CUSTOM_API_KEY` or describe the per-agent `.env`/tokens
   duplication (table above). Where a stale reference breaks the render path
   itself (standalone compose env mapping, `.env.example`), aligning it is part
   of the closeout so the verification passes.

## Acceptance criteria

- **AC1 (verify, default compose):** `docker compose -f docker-compose.yml up -d`
  with `DEEPSEEK_API_KEY` in `.env` → every agent's `/opt/data/config.yaml`
  contains `deepseek-v4-flash` + `https://api.deepseek.com/v1` and a **resolved**
  key (no literal `${…}` placeholder); per-agent LLM ping
  (`hermes chat -q "Reply with exactly: OK"`) returns OK for all four roles.
- **AC2 (verify, standalone):** `docker compose -f docker-compose.standalone.yml
  up -d` renders the same; the compose env mapping matches the templates
  (`DEEPSEEK_API_KEY`, no `CUSTOM_API_KEY`).
- **AC3 (verify, office overlay / SSOT path):** on a composed instance running
  the office overlay (live instances, `TOKENS_FILE=tokens.yaml`), config renders
  from the SSOT at container start and agents answer the ping. Evidence
  recorded on issue #40.
- **AC4 (smoke check docs):** template bring-up docs (README quick start /
  architecture) end with a documented smoke check covering every agent; it fails
  loudly when an agent cannot reach the LLM.
- **AC5 (stale refs):** `grep -rn "runinfra\|qwen\|CUSTOM_API_KEY"` over
  README, docs/, `.env.example`, compose files, and `crew/*.py` returns nothing
  that names the LLM key; no doc describes per-agent `.env`/tokens key
  duplication. (Intentional legacy-history notes may remain if explicitly
  marked.)

## Locked calls

- No change to the already-merged render mechanism (#37/#45) beyond aligning
  stale references that break it (standalone env mapping, `.env.example`).
- Verification evidence lands on issue #40 (concrete commands + observed
  output), not just a prose "works".
- The smoke check is **documentation** in the template repo (mirroring office
  `scripts/smoke.py`); adding a runnable template script is optional and out of
  the minimal closeout scope.
- No capability contract changes: the change record is proposal + tasks with
  acceptance criteria (no `openspec/specs/*` delta).

## Out of scope

- Dashboard per-agent "LLM reachable" indicator (issue #40's optional item 3).
- Re-architecting template composes to mount `tokens.yaml` directly (the office
  overlay already provides the strict SSOT path on live instances).
- Batch C's docs alignment (completion_watcher / shared-workspace clone model) —
  separate spec, separate PR.
