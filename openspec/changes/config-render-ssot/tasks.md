# Tasks: config-render-ssot (#40 closeout)

## 1. Spec (this PR)

- [x] 1.1 `proposal.md` — closeout scope + acceptance criteria
- [x] 1.2 `design.md` — verification evidence + decisions D1–D4
- [x] 1.3 `specs/layer-separation/spec.md` — rendered-instance-config requirement
- [x] 1.4 `tasks.md`

## 2. Closeout implementation (follow-up PR, after this spec merges)

- [ ] 2.1 **Verify render-from-SSOT end-to-end on a composed instance** (D4):
      for each agent, confirm `config.yaml` is fully rendered (no literal
      `${VAR}`), `.env` carries the SSOT header, and an LLM round-trip returns
      exactly `OK`. Refresh the evidence table in `design.md` or link the run
      output from the PR.
- [ ] 2.2 **Bring-up smoke in the template docs** (D1): replace/extend the
      README quick-start ping with the per-agent round-trip
      (`docker exec dev-crew-<role> hermes chat -q "Reply with exactly: OK"`),
      state that office-composed instances use the overlay's `scripts/smoke.py`,
      and remove any wording that treats a green `docker ps` as "up".
- [ ] 2.3 **`.env.example` stale LLM section** (D3): drop the runinfra comment,
      state DeepSeek, declare the single unified `CUSTOM_API_KEY`.
- [ ] 2.4 **Unify the LLM env key** (D3): `CUSTOM_API_KEY` in `.env.example`,
      `docker-compose.yml`, `docker-compose.standalone.yml`, and all four
      `agents/<role>/hermes-home/config.yaml.template` files.
- [ ] 2.5 **Remaining stale claims** (D2): correct any passage in `README.md`,
      `docs/architecture.md`, `docs/office-template.md` that implies the template
      composes read `tokens/tokens.yaml` directly or that keys are duplicated
      per agent in `.env` (office-template env-var table rows sourced from
      `tokens.yaml` under Office).
- [ ] 2.6 **Standalone smoke passes**: a fresh `cp .env.example .env` +
      standalone compose boot ends with every agent answering `OK`.
- [ ] 2.7 **Grep clean**: `grep -riE 'runinfra|qwen'` matches nothing in the
      repo (docs, `.env.example`, templates, composes).
