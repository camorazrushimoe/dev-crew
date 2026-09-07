# Design: SSOT config render closeout

## What "verified end-to-end" means

Verified means: on a running composed instance, each agent's rendered
`/opt/data/config.yaml` carries real credentials (no literal `${VAR}`), the
per-agent environment is written from the SSOT, and an LLM round-trip succeeds
for every agent.

### Evidence (live `dev-1` instance, 2026-09-07)

| Check | Result |
|---|---|
| `config.yaml` rendered | `/opt/data/config.yaml` exists with `model.default: deepseek-v4-flash`, `base_url: https://api.deepseek.com/v1`, populated `api_key` |
| `.env` provenance | `/opt/data/.env` header: *"Managed by office/render_config.py — do not edit by hand."* / *"Secrets come from the single source of truth: tokens/tokens.yaml."* (0600) |
| SSOT key resolution | `tokens/tokens.yaml` → `llm.base_url` + `llm.factories.dev-crew`; identity via `FACTORY_NAME=dev-crew`, `TEAM_NAME=dev-1`, `AGENT_ID=tech-pm` |
| LLM round-trip | agent answers (this session runs on the rendered config) |
| Failure mode | office `render_config.py` exits 2 on a missing placeholder instead of booting a gateway with a literal `${VAR}` |

## The two render paths (docs must not conflate them)

1. **Template composes** (`docker-compose.yml`, `docker-compose.standalone.yml`):
   `crew/render_config.py` substitutes `${VAR}` from the container environment at
   start; the compose sources those values from the instance `.env` (gitignored).
   This is instance-config-by-`.env`, by design — the template is a foundation
   repo and cannot know an instance's secrets.
2. **Live office-composed instances**: the Office overlay
   (`office/render_config.py`) resolves `FACTORY_NAME` / `TEAM_NAME` / `AGENT_ID`
   against `tokens/tokens.yaml` — the single source of truth — and renders the
   same `config.yaml.template` plus the per-agent `$HERMES_HOME/.env` (0600).
   Provider/key changes propagate on restart; no per-agent duplication exists.

The strict `tokens.yaml` SSOT therefore exists via the Office overlay on live
instances; the template composes document `.env` sourcing. #40's original
"adopt the overlay into the template" proposal was re-scoped: the root fix
(#37/#45) stands, and this change verifies + documents rather than relocating
the SSOT boundary.

## Decisions

### D1 — Smoke check = per-agent LLM round-trip, documented as the last bring-up step

`docker exec dev-crew-<role> hermes chat -q "Reply with exactly: OK"` for every
agent, failing loudly; office-composed instances additionally use the overlay's
`scripts/smoke.py`. Rationale: this is exactly the call that failed with the 403
in #40 — passing it for all agents means the crew is *usable*, not merely *up*.
The README's current single-agent `hermes chat -q "hello"` step is upgraded to
the full per-agent round-trip and moved to the end of bring-up.

### D2 — Docs state both render paths accurately

No passage may claim the template composes read `tokens/tokens.yaml` directly,
or that keys are duplicated per agent in `.env`. Template = instance `.env`;
SSOT = Office overlay on live composed instances.

### D3 — Unify the LLM key name on `CUSTOM_API_KEY` across the template family

Chosen name: `CUSTOM_API_KEY` (as today in `.env.example` and the standalone
compose).

- All four `config.yaml.template` files reference `${CUSTOM_API_KEY}`.
- Both composes pass `CUSTOM_API_KEY=${CUSTOM_API_KEY:-}` from the instance
  `.env`.
- `.env.example` declares `CUSTOM_API_KEY` and drops the runinfra comment.
- The Office overlay already resolves `tokens/tokens.yaml` →
  `CUSTOM_API_KEY`/`OPENROUTER_API_KEY` per factory, so a placeholder of
  `${CUSTOM_API_KEY}` keeps working on live office-composed instances at any
  template ref — including instances whose templates are older than #45.

Rejected alternative: unify on `DEEPSEEK_API_KEY` (as #45 named it in the
default compose). It would require the Office overlay and already-deployed
instance templates to be renamed too — a cross-repo change that breaks the
"SSOT renders any pinned ref" property this closeout is meant to guarantee.

### D4 — Verification results land back in this change

The closeout implementation PR reports the evidence-table refresh (or a pointer
to the run output) as a comment/update, so "verified end-to-end" is repeatable,
not a one-off claim.

## Risks

- **Standalone bring-up currently does not render** (its compose passes
  `CUSTOM_API_KEY` while main's templates reference `${DEEPSEEK_API_KEY}`): the
  smoke step exists precisely to catch this; D3 removes the mismatch. This is
  the one code-adjacent cleanup in scope, and it is a key-name alignment, not a
  behaviour change.
- Docs-only fixes rot again: the smoke step and D2 wording are what make the
  failure mode visible next time the provider moves.
