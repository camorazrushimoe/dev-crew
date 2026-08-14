# Dev Crew — architecture

> Draft. Refined as requirements evolve.

## Overview

A team of isolated agents (one Docker container each) plus shared infrastructure,
orchestrated as a single Docker Compose project.

```mermaid
flowchart TB
    M["Human / Manager"] --> E["single entry point<br/>crew-send.py"]

    subgraph Team["dev-crew (one Docker project)"]
        subgraph Agents["Engineering agents"]
            D["developer"]
            Q["qa"]
            T["tech-pm"]
        end
        B[("shared-memory<br/>Redis — bus + state")]
        subgraph Clusters["Universal clusters"]
            DC[("dev-cluster<br/>postgres-dev + neo4j-dev")]
            SC[("staging-cluster<br/>postgres-staging + neo4j-staging")]
        end
    end

    E -->|"task"| T

    D <-->|"direct (webhook door)"| Q
    Q <-->|"direct (webhook door)"| T
    T <-->|"direct (webhook door)"| D

    D <-->|"events / status"| B
    Q <-->|"events / status"| B
    T <-->|"events / status"| B

    D -->|"builds in"| DC
    Q -->|"verifies in"| SC
```

## Components

- **Agents** — isolated containers, each with its own Hermes runtime, tools and SOUL.
- **shared-memory** — Redis: message bus (pub/sub + inbox queues) and shared state.
- **entry point** — `crew-send.py` signs a message and POSTs it to any agent's webhook door.
- **workspace** — a shared bind-mounted directory (`./workspace:/workspace`) where code lives.
  Developer and qa have read/write, tech-pm read-only.
- **Universal clusters** — project-agnostic dev/staging environments (see below).

## Contracts

1. **LLM API** — OpenAI-compatible (`OPENAI_BASE_URL` + `OPENAI_API_KEY` + model).
2. **Message envelope** — `bus/action-schema.json` (`actor` / `action` / `target` / `payload` / `timestamp`).
3. **Tokens** — `tokens/tokens.yaml` (real values, gitignored), mounted read-only per agent.
4. **Door** — each agent exposes `POST /webhooks/inbox`, HMAC-SHA256 signed (`X-Hub-Signature-256`).

## Communication

- **Human/manager → agent** — `crew-send.py <agent> "<message>"` (host) or from any container.
- **Agent → agent** — same door, using container DNS: `crew-send.py <agent> "<message>" --container`.
- **Agent → bus** — publish events/status to Redis (the action registry).
- **Discussion channel** — Linear ticket comments are the source of truth for task decisions
  (persistent, human-visible, searchable). Redis is the signal/notification layer, not the record.

## Planning gate (discuss before code)

Every task passes through a planning phase before execution. The rule is encoded in
each agent's SOUL (`Planning gate` section):

```
task (Linear ticket)
   → tech-pm writes a PLAN as a ticket comment (approach, assumptions, risks, subtasks)
   → developer + qa review the plan in the comments (flag wrong assumptions)
   → manager explicitly approves (comment "go"/"approved")  ← manual gate
   → developer implements (feature branch → PR)
   → qa verifies against the approved plan in staging-cluster
   → completion: comment + state change in Linear, ping manager
```

No code is written until the plan is approved. This prevents agents from working
hard on wrong assumptions.

## Universal clusters (project-agnostic)

Two isolated environments, shared by every project. Clusters start **empty** — each
project creates its own database/schema inside them (no per-project containers).

| Cluster | Services | Host ports | Purpose |
|---------|----------|------------|---------|
| dev-cluster | `postgres-dev`, `neo4j-dev` | 5433 / 7475+7688 | developer builds and breaks freely |
| staging-cluster | `postgres-staging`, `neo4j-staging` | 5434 / 7476+7689 | qa verifies release candidates |

Agents reach them over the `crew` network via environment variables:
`DEV_POSTGRES_URL`, `STAGING_POSTGRES_URL`, `DEV_NEO4J_URI` + `DEV_NEO4J_AUTH`,
`STAGING_NEO4J_URI` + `STAGING_NEO4J_AUTH`. Credentials default in compose and are
overridable via `.env` (see `.env.example`).

## Foundation vs instance vs project (separation of concerns)

The factory is a **template**: one versioned repo that can be cloned into any number of
running instances. Three layers exist and must never mix.

### 1. Foundation — the template (versioned, shared)

Who the agents ARE and what they CAN do. Lives in this repo, tracked by git, updated
by `git pull`. Identical across every instance.

| Concern | Location |
|---|---|
| Identity (role) | `agents/<name>/hermes-home/SOUL.md` |
| Capabilities | `agents/<name>/skills/` |
| Team + infra definition | `docker-compose.yml` |
| Communication protocol | `crew/`, `bus/` |
| Docs | `docs/`, `README.md` |

### 2. Instance config — per-machine (gitignored)

Secrets and addresses that differ per running instance. Never committed.

| Concern | Location |
|---|---|
| Cluster passwords | `.env` (template: `.env.example`) |
| Agent tokens | `tokens/tokens.yaml` |
| Door registry (HMAC secrets + URLs) | `crew/agents.json` |

### 3. Project work — what agents produce (outside the foundation)

The code, data and backlog of the products the factory builds. Never enters this repo.

| Concern | Location |
|---|---|
| Project code | `workspace/<project>/` (its own git repo) |
| Project data | cluster volumes (its own schema/DB inside the shared clusters) |
| Project backlog | a **separate Linear project** |

### Update flow (foundation upgrades don't touch project work)

```
foundation change → PR → merge on GitHub → git pull on an instance
   → agents reload SOUL/skills ("become smarter")
project work is untouched: workspace/, cluster data, and Linear projects are separate
```

### Agent self-awareness

An agent's context is assembled from the layers, nothing project-specific is baked in:

- **WHO I am** → `SOUL.md` (foundation)
- **WHAT I can do** → skills (foundation)
- **WHERE the infra is** → env vars: cluster URLs, workspace path (instance config)
- **WHAT to do now** → the Linear ticket (project, arrives with each dispatch)

Project context arrives per-task; the foundation stays project-agnostic.

## Open questions

- What exactly agents write to shared memory (granularity of the bus).
- Whether the planning gate stays manual or becomes auto-approve after agreement.
- Whether projects need additional cluster services (message queue, object storage).
