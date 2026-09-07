## Purpose

Close the #40 failure mode: instance agent configs are rendered at container
start from a template — never hand-maintained per instance — so provider/key
changes propagate instead of silently rotting until the first real LLM call.

## ADDED Requirements

### Requirement: Rendered instance config

Agent runtime config (`agents/<role>/hermes-home/config.yaml`) SHALL be rendered
from `config.yaml.template` at container start by the render entrypoint, never
hand-maintained per instance. In template composes the renderer substitutes
instance-`.env` values into the template. On Office-composed instances the
Office overlay SHALL render the same template from the `tokens/tokens.yaml`
single source of truth, resolving the agent's identity via `FACTORY_NAME` /
`TEAM_NAME` / `AGENT_ID`, and SHALL write the resolved per-agent environment
(`$HERMES_HOME/.env`, 0600) from the same source.

#### Scenario: provider migration reaches an agent

- **WHEN** the LLM provider or key changes in the instance SSOT (`tokens.yaml`
  on Office-composed instances; `.env` on template composes)
- **THEN** an agent container restart SHALL render a config with the new
  provider and key
- **AND** no literal `${VAR}` placeholder SHALL remain in the rendered
  `config.yaml`

#### Scenario: bring-up smoke

- **WHEN** a factory instance is brought up
- **THEN** bring-up SHALL include a per-agent LLM round-trip smoke check that
  fails loudly
- **AND** the instance SHALL NOT be declared up on container status alone
