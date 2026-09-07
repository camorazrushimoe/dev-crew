# Design: Config render from tokens.yaml SSOT — closeout approach

## D1 — What the fix already is (do not re-fix)

Root fix merged: config.yaml.template per agent + render_config.py at container
start (both composes, #37) and DeepSeek templates/env (#45). This change does
not touch the render mechanism; it verifies it end-to-end and aligns the
surrounding docs/templates.

## D2 — Verification matrix

| Path | Instance | Key source | Verify by |
|---|---|---|---|
| Office overlay (strict SSOT) | live composed instance (office composes a dev-crew instance from this template) | `tokens/tokens.yaml` SSOT → identity resolution (`FACTORY_NAME`/`TEAM_NAME`/`AGENT_ID`) → rendered `config.yaml` + `.env` | container start renders; per-agent LLM ping OK |
| Template default compose | `docker-compose.yml` (Office-attached) | instance `.env` (`DEEPSEEK_API_KEY`) via compose env → `crew/render_config.py` | `docker compose up -d`; inspect rendered `config.yaml`; per-agent LLM ping |
| Template standalone compose | `docker-compose.standalone.yml` | instance `.env` — **currently stale: passes `CUSTOM_API_KEY`** | fix env mapping → `docker compose -f docker-compose.standalone.yml up -d`; same checks |

Verification evidence for each row: (a) rendered `/opt/data/config.yaml` shows
`api.deepseek.com` + resolved key (no `${…}` placeholder), (b) LLM ping answers
"OK" for all four roles.

## D3 — Smoke check documentation (template)

Office ships `scripts/smoke.py` (levels 0–3: static → infra → bus → doors) +
`smoke.sh`. The template has only an ad-hoc README ping. Closeout: document a
bring-up smoke step in the template README (and architecture doc where the
bring-up is described) that mirrors the office pattern for the template's own
scope (containers up → per-agent LLM ping; fail loudly, exit non-zero). The doc
SHALL state that a green `docker ps` is not "factory up" until the smoke check
passes.

## D4 — Stale-reference cleanup list (docs/templates)

1. `docker-compose.standalone.yml` — env `CUSTOM_API_KEY` → `DEEPSEEK_API_KEY`
   (×4) + header comment.
2. `.env.example` — LLM section: drop runinfra + `CUSTOM_API_KEY`; document
   `DEEPSEEK_API_KEY`; drop any per-agent duplication wording.
3. `docker-compose.yml` — comment line naming `${CUSTOM_API_KEY}` → align with
   `DEEPSEEK_API_KEY` (env already correct).
4. `crew/render_config.py` — module docstring: `${CUSTOM_API_KEY}` →
   `${DEEPSEEK_API_KEY}` (comment-only change).
5. `docs/office-template.md` — env-var list: `CUSTOM_API_KEY` →
   `DEEPSEEK_API_KEY`.
6. `docs/architecture.md` — Contract 3 + instance-config table: replace
   "tokens.yaml mounted read-only per agent" with the actual two-path model
   (template composes read instance `.env`; office overlay resolves a single
   `tokens.yaml` SSOT by agent identity).
7. `tokens/tokens.example.yaml` — either align with the SSOT schema used by the
   office overlay or mark the per-agent section model as legacy; no doc may
   present duplicated per-agent keys as the live model.

Boundary rule: docs/templates may name the retired model only in an explicit
"legacy/history" note with a pointer to the current path. No runtime code
changes beyond aligning the standalone compose env mapping and `.env.example`
(those are part of making the closeout verifiable, AC1–AC5).
