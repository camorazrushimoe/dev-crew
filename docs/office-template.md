# Dev Crew as an Agent Office template

This repository is the **template** for Dev team instances under [Agent Office](https://github.com/camorazrushimoe/agent-office).

Agent Office is a multi-repo system:

- **agent-office** — shell (Office agents, shared Redis bus, shared pre-prod, composition)
- **dev-crew** (this repo) — template for implementation teams
- **lab-crew** — template for research teams

Operators clone Office, then spawn as many Dev instances as they need from pinned refs of this template (e.g. 1, 2, or 4 Dev teams).

Full composition model: [agent-office/docs/composition.md](https://github.com/camorazrushimoe/agent-office/blob/main/docs/composition.md)

## What changes when running under Office

| Standalone Dev Crew (today) | Under Agent Office |
|-----------------------------|--------------------|
| Local Redis (`shared-memory`) | **Office shared Redis bus** |
| Local staging-env as team-owned pre-prod style gate | **Office shared pre-prod** (Super DevOps) |
| Agents `restart: unless-stopped` | **Idle stop + wake-on-demand** (lifecycle controller) |
| Self-contained factory | **Instance** of a template, registered in Office |

What **stays** in this template:

- Roles: developer, qa, tech-pm, devops
- SOULs, skills, OpenSpec for software delivery
- **Private dev-cluster** (team-owned sandbox)
- Webhook doors + send client (must become wake-aware)
- Workspace / project attach pattern

## Template contract (Office-compatible mode)

When composed under Office, this template MUST:

1. Connect all agents to the **external** Office Redis URL (no default private inter-agent bus).
2. Keep HMAC webhook doors; send path MUST **wake** a stopped target before POST.
3. Emit Office-compatible bus events (`agent.started` / `agent.stopped`, task/handoff signals as applicable), with team-qualified actor ids when multiple instances exist (e.g. `dev-1/developer`).
4. Run a **lifecycle controller** for this instance’s agent containers (idle ~40m, wake on demand). See Office `docs/agent-lifecycle.md`.
5. Use controller-managed restart policy for agents (`restart: "no"`).
6. **Not** own shared pre-prod; promotions go through Office Super DevOps rules.
7. Be registrable: name, type=`dev`, door/health/lifecycle endpoints, template ref.

Migration detail (Office side): [migration-teams-to-office-bus.md](https://github.com/camorazrushimoe/agent-office/blob/main/docs/migration-teams-to-office-bus.md)

## Standalone mode

This repo MAY continue to support standalone operation (local Redis, always-on agents) for developing the template itself.

**Default for Office operators is Office-attached mode.** Standalone is not required to run a composed Office.

## Implementation roadmap (spec → code)

This document is the **specification commitment**. Code changes still required:

- [ ] Optional/external Redis configuration (Office bus URL)
- [ ] Lifecycle controller service + agent `restart: "no"`
- [ ] Wake-aware `crew/crew-send.py`
- [ ] Busy lock tied to task start/finish hooks
- [ ] Team-qualified actor names on the bus when `TEAM_NAME` is set
- [ ] Document env vars for Office attach (bus, team name, pre-prod network)
- [ ] Align staging-env usage with “private verify” vs Office pre-prod promotion

## Versioning

- Pin instances to **tags** of this repo in production compositions.
- Breaking Office protocol changes should be noted as: `Office compatibility: requires agent-office ≥ x.y`.

## Related

- [Agent Office](https://github.com/camorazrushimoe/agent-office)
- [Lab Crew template](https://github.com/camorazrushimoe/lab-crew)
- Factory standard in this repo: `crew/FACTORY-STANDARD.md`
