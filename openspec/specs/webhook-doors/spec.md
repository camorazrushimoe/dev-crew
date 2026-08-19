# Webhook Doors

## ADDED Requirements

### Requirement: Inbox door

Each agent SHALL expose a `POST /webhooks/inbox` endpoint on container port
`8644`, mapped to its distinct host port (developer 8651, qa 8652, tech-pm 8653,
devops 8654).

### Requirement: HMAC signature

Messages SHALL be signed with HMAC-SHA256 over the raw request body, sent in the
`X-Hub-Signature-256` header as `sha256=<hexdigest>`.

#### Scenario: a validly signed message is accepted

- **WHEN** a message with a valid `X-Hub-Signature-256` arrives
- **THEN** the agent SHALL accept it and process it asynchronously (202)

#### Scenario: an unsigned or mis-signed message is rejected

- **WHEN** a message has a missing or invalid signature
- **THEN** the agent SHALL reject it

### Requirement: Door registry

The door registry SHALL map each agent to `host_url`, `container_url`, and
`secret`. The real registry lives in `crew/agents.json` (gitignored); the
template in `crew/agents.example.json` SHALL be committed.

### Requirement: Door client

`crew/crew-send.py` SHALL send a signed message to any agent — from the host via
`host_url`, or from inside the network via `container_url` (with `--container`).

#### Scenario: manager sends a task from the host

- **WHEN** the manager runs `python3 crew/crew-send.py <agent> "<message>"`
- **THEN** the client SHALL sign and POST the message and report the 202 receipt

#### Scenario: agent addresses another agent in-container

- **WHEN** an agent runs `crew-send.py <agent> "<message>" --container`
- **THEN** the client SHALL resolve the target via `container_url` on the `crew` network
