#!/usr/bin/env python3
"""Container entrypoint helper — render secrets into config.yaml.

The gateway config loader does NOT expand ${VAR} references in webhook route
secrets (only the hermes_cli.config.load_config path does for the model block).
So we render them at container start: config.yaml.template holds
${DOOR_SECRET} and ${CUSTOM_API_KEY}, this script substitutes them from the
environment and writes the final /opt/data/config.yaml.

Secrets live ONLY in the gitignored .env; neither the template nor the
rendered file is committed.
"""
import os
import re
import sys

TEMPLATE = "/opt/data/config.yaml.template"
TARGET = "/opt/data/config.yaml"


def render() -> None:
    with open(TEMPLATE, encoding="utf-8") as f:
        text = f.read()

    def sub(m: re.Match) -> str:
        var = m.group(1).strip()
        val = os.environ.get(var)
        if val is None:
            print(f"[render-config] WARNING: {var} not set in env", file=sys.stderr)
            return m.group(0)
        return val

    rendered = re.sub(r"\$\{([A-Z_][A-Z0-9_]*)\}", sub, text)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"[render-config] wrote {TARGET} ({len(rendered)} bytes)")


if __name__ == "__main__":
    render()
