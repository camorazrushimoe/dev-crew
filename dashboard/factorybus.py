#!/usr/bin/env python3
"""Dev Crew — shared bus + Linear client (stdlib only, no dependencies).

Used by the dashboard reporter and the completion watcher. Kept in one
module so the Redis RESP client and the Linear GraphQL client are defined
once and shared, instead of being copy-pasted per script.

Conventions:
  * Bus events follow bus/action-schema.json and land on Redis list
    `bus:events` (LPUSH) + pub/sub channel `bus:events`.
  * Linear is the durable record; the bus is the signal layer.
"""
import json
import os
import hmac
import hashlib
import socket
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Instance config (env, with sensible Dev Crew defaults)
# ---------------------------------------------------------------------------

AGENTS_BASE = os.environ.get(
    "AGENTS_BASE", os.path.expanduser("~/Projects/dev-crew/agents")
)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

LINEAR_URL = "https://api.linear.app/graphql"
# Team "Bonny factory", key BON (stable instance config).
LINEAR_TEAM_ID = os.environ.get(
    "LINEAR_TEAM_ID", "ed41926c-40e3-43a4-8c79-469c7ac223c1"
)
# Workflow state ids for team BON. Overridable via env.
LINEAR_STATES = {
    "in_progress": os.environ.get(
        "LINEAR_STATE_IN_PROGRESS", "7f89ffb6-3edb-4611-9380-91b8c5678aed"
    ),
    "done": os.environ.get(
        "LINEAR_STATE_DONE", "2845cb2f-8080-47db-9cd0-7dd00f70e2e2"
    ),
    "in_review": os.environ.get(
        "LINEAR_STATE_IN_REVIEW", "9faf881e-7305-4093-894f-a44f0f05be2a"
    ),
    # Team BON has no "Blocked" state. Leave empty -> no state move on failure.
    "blocked": os.environ.get("LINEAR_STATE_BLOCKED", ""),
}

# ---------------------------------------------------------------------------
# Minimal RESP (Redis) client
# ---------------------------------------------------------------------------
class Redis:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.host, self.port = host, port

    def _read_n(self, f, n):
        buf = b""
        while len(buf) < n:
            chunk = f.read(n - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf

    def _read(self, f):
        line = f.readline()
        if not line:
            return None
        b = line[:1]
        if b == b"+":
            return line[1:-2].decode()
        if b == b"-":
            return line[1:-2].decode()
        if b == b":":
            return int(line[1:-2])
        if b == b"$":
            n = int(line[1:-2])
            if n == -1:
                return None
            data = self._read_n(f, n)
            f.read(2)  # trailing CRLF
            return data.decode(errors="replace")
        if b == b"*":
            n = int(line[1:-2])
            return [self._read(f) for _ in range(n)]
        return None

    def cmd(self, *args):
        try:
            s = socket.create_connection((self.host, self.port), timeout=3)
        except OSError:
            return None
        parts = [f"*{len(args)}\r\n".encode()]
        for a in args:
            a = str(a).encode()
            parts.append(f"${len(a)}\r\n".encode() + a + b"\r\n")
        s.sendall(b"".join(parts))
        f = s.makefile("rb")
        r = self._read(f)
        f.close()
        s.close()
        return r


# ---------------------------------------------------------------------------
# Bus envelope + publish
# ---------------------------------------------------------------------------
def envelope(actor, action, target, payload):
    """Build a message conforming to bus/action-schema.json."""
    return {
        "id": str(uuid.uuid4()),
        "actor": actor,
        "action": action,
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload or {},
    }


def publish(redis, actor, action, target="*", payload=None):
    """Publish an action to the bus (list + pub/sub). Returns the message."""
    msg = envelope(actor, action, target, payload)
    raw = json.dumps(msg)
    redis.cmd("LPUSH", "bus:events", raw)
    redis.cmd("LTRIM", "bus:events", 0, 499)
    redis.cmd("PUBLISH", "bus:events", raw)
    return msg


# ---------------------------------------------------------------------------
# Linear GraphQL client
# ---------------------------------------------------------------------------
_ENV_FILES = [
    os.path.expanduser("~/Projects/dev-crew/.env"),
    os.path.join(AGENTS_BASE, "tech-pm", "hermes-home", ".env"),
    os.path.join(AGENTS_BASE, "developer", "hermes-home", ".env"),
]


def getenv(key, default=""):
    """Config lookup: process env first, then the instance .env files."""
    v = os.environ.get(key)
    if v:
        return v
    for path in _ENV_FILES:
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "="):
                        val = line.split("=", 1)[1].strip()
                        if val:
                            return val
        except OSError:
            continue
    return default


def sign(secret, payload):
    """HMAC-SHA256 signature in X-Hub-Signature-256 format."""
    return "sha256=" + hmac.new(secret.encode(), payload.encode(),
                                hashlib.sha256).hexdigest()


def load_linear_key():
    """LINEAR_API_KEY from env, then instance .env files."""
    return getenv("LINEAR_API_KEY", "")


class Linear:
    def __init__(self, key=None):
        self.key = key if key is not None else load_linear_key()

    @property
    def configured(self):
        return bool(self.key)

    def gql(self, query, variables=None):
        if not self.key:
            return {"errors": [{"message": "LINEAR_API_KEY not configured"}]}
        body = json.dumps({"query": query, "variables": variables or {}})
        req = urllib.request.Request(
            LINEAR_URL,
            data=body.encode(),
            method="POST",
            headers={"Authorization": self.key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"HTTPError": e.code, "body": e.read().decode()}
        except urllib.error.URLError as e:
            return {"URLError": str(e.reason)}

    def issue_id(self, identifier):
        """Resolve an issue identifier (e.g. BON-27) to its UUID."""
        r = self.gql(
            "query($id: String!) { issue(id: $id) { id identifier state { name } } }",
            {"id": identifier},
        )
        if "errors" in r or not r.get("data", {}).get("issue"):
            return None
        return r["data"]["issue"]["id"]

    def move_state(self, issue_id, state_id):
        if not state_id:
            return None
        r = self.gql(
            "mutation($id: String!, $stateId: String!) "
            "{ issueUpdate(id: $id, input: { stateId: $stateId }) "
            "{ issue { identifier state { name } } } }",
            {"id": issue_id, "stateId": state_id},
        )
        return r

    def comment(self, issue_id, body):
        r = self.gql(
            "mutation($id: String!, $body: String!) "
            "{ commentCreate(input: { issueId: $id, body: $body }) { success } }",
            {"id": issue_id, "body": body},
        )
        return r

    def projects(self):
        """List Linear Projects (id, name, url, issue count)."""
        q = """
        query {
          projects(first: 50) { nodes { id name url
            issues { nodes { id } }
          } }
        }
        """
        r = self.gql(q)
        nodes = r.get("data", {}).get("projects", {}).get("nodes", [])
        out = []
        for n in nodes:
            out.append({
                "id": n.get("id"),
                "name": n.get("name"),
                "url": n.get("url"),
                "issue_count": len((n.get("issues") or {}).get("nodes", [])),
            })
        return out

    def project_issues(self, project_name):
        """Tickets in a Linear Project (matched by name), for the run view."""
        q = """
        query {
          projects(first: 50) { nodes { id name url
            issues { nodes { identifier title state { name } assignee { name } } }
          } }
        }
        """
        r = self.gql(q)
        nodes = r.get("data", {}).get("projects", {}).get("nodes", [])
        for n in nodes:
            if n.get("name") == project_name:
                return n
        return None
