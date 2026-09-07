# Tasks: Config render from SSOT — verify + closeout

Implementation checklist for the PR that follows this spec (Batch B). Order
matters; keep each step verifiable against the acceptance criteria (AC1–AC5).

## 1. Align stale references (AC5 prerequisite, before verification)

- [ ] `docker-compose.standalone.yml`: replace `CUSTOM_API_KEY=${CUSTOM_API_KEY:-}`
      with `DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}` in all four services; fix the
      header comment (names `${CUSTOM_API_KEY}` today).
- [ ] `.env.example`: replace the "runinfra" LLM section + `CUSTOM_API_KEY=` with
      a DeepSeek section documenting `DEEPSEEK_API_KEY` (one shared key, all
      agents). Remove any per-agent duplication wording.
- [ ] `docker-compose.yml`: header comment line naming `${CUSTOM_API_KEY}` →
      `${DEEPSEEK_API_KEY}` (env block already correct).
- [ ] `crew/render_config.py`: module docstring `${CUSTOM_API_KEY}` →
      `${DEEPSEEK_API_KEY}` (comment-only).
- [ ] `docs/office-template.md`: env-var list `CUSTOM_API_KEY` →
      `DEEPSEEK_API_KEY`.
- [ ] `docs/architecture.md`: Contract 3 "Tokens" + instance-config table —
      replace "tokens/tokens.yaml mounted read-only per agent" with the current
      two-path model (template composes read instance `.env`; office overlay
      resolves a single `tokens.yaml` SSOT by agent identity at container start).
- [ ] `tokens/tokens.example.yaml`: align with the SSOT schema or mark the
      per-agent-section model as legacy with a pointer to the current path.
- [ ] Grep gate: `grep -rn "runinfra\|qwen\|CUSTOM_API_KEY"` over README, docs/,
      `.env.example`, `docker-compose*.yml`, `crew/*.py` → no live-model hits
      (explicit legacy notes allowed).

## 2. Verification run (AC1–AC3)

- [ ] **Default compose (AC1):** with `DEEPSEEK_API_KEY` set in `.env`, run
      `docker compose up -d`; for each agent confirm `/opt/data/config.yaml` was
      rendered at start from `config.yaml.template` and contains
      `api.deepseek.com` + resolved key (no `${…}`); ping
      `docker exec <name> hermes chat -q "Reply with exactly: OK"` → OK for all
      four roles.
- [ ] **Standalone compose (AC2):** `docker compose -f docker-compose.standalone.yml
      up -d`; same checks after the env-mapping fix above.
- [ ] **Office overlay / strict SSOT (AC3):** on a composed instance running the
      office overlay (`TOKENS_FILE=tokens.yaml`), confirm config renders from the
      SSOT at container start and the LLM ping answers OK.
- [ ] Record evidence on issue #40: commands run, rendered-config excerpt
      (keys redacted), ping results per role. State explicitly which path each
      evidence item covers.

## 3. Bring-up smoke check docs (AC4)

- [ ] README quick start (or the bring-up section it points to): replace the
      single ad-hoc ping with a documented smoke step covering every agent
      (mirror office `scripts/smoke.py` for the template's scope); a non-OK ping
      SHALL fail loudly (non-zero) instead of "factory is up".
- [ ] State in the docs that a green `docker ps` is not sufficient — the LLM
      ping is the bring-up gate.

## 4. Final acceptance sweep

- [ ] AC1–AC5 all pass; re-run the grep gate from step 1.
- [ ] No runtime code changes beyond the aligned env mapping / `.env.example`
      (render mechanism itself untouched).
- [ ] Update issue #40 with the verification evidence + closeout note.
