#!/usr/bin/env python3
"""Dev Crew — observability dashboard.

A reporter thread polls each agent's health endpoint + gateway log, writes
status + activity to Redis (the shared-memory bus), and a tiny web server
renders a live team view.

Usage:  python3 dashboard/app.py   (then open http://localhost:8660)
Zero dependencies — stdlib only.
"""
import os
import re
import json
import time
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

import factorybus

BASE = os.path.expanduser("~/Projects/dev-crew/agents")
AGENTS = {
    "developer": ("Dev Crew Developer", 8651),
    "qa":         ("Dev Crew QA", 8652),
    "tech-pm":    ("Dev Crew Tech PM", 8653),
    "devops":     ("Dev Crew DevOps", 8654),
}
REDIS_HOST = "localhost"
REDIS_PORT = 6379
PORT = 8660
POLL_INTERVAL = 2.0

linear = factorybus.Linear()


# --- Minimal RESP (Redis) client, stdlib only -----------------------------
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


redis = Redis()

INBOUND_RE = re.compile(r"inbound message:.*?msg='(.*?)'")
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")


def log_tail(agent, n=400):
    p = os.path.join(BASE, agent, "hermes-home", "logs", "agent.log")
    try:
        with open(p, "r", errors="replace") as f:
            return f.readlines()[-n:]
    except OSError:
        return []


def poll_agent(agent, port):
    # liveness
    alive = False
    try:
        with urlopen(f"http://localhost:{port}/health", timeout=3) as resp:
            alive = resp.status == 200
    except Exception:
        alive = False

    # activity from the gateway log
    lines = log_tail(agent)
    state = "idle"
    task = None
    events = []
    last_ts = None
    for ln in lines:
        m = TS_RE.search(ln)
        ts = m.group(1) if m else None
        if ts:
            last_ts = ts
        if "inbound message:" in ln:
            state = "working"
            mm = INBOUND_RE.search(ln)
            task = mm.group(1) if mm else None
            if ts:
                events.append({"ts": ts, "type": "inbound", "text": task or ""})
        elif "response ready:" in ln:
            state = "idle"
            if ts:
                events.append({"ts": ts, "type": "response", "text": ln.split("response=")[-1].strip() if "response=" in ln else ""})
    if not alive:
        state = "down"

    status = {
        "agent": agent,
        "name": AGENTS[agent][0],
        "state": state,
        "alive": alive,
        "task": task,
        "updated_at": int(time.time()),
    }
    # write status + activity to Redis (the bus)
    redis.cmd("SET", f"status:{agent}", json.dumps(status))
    redis.cmd("EXPIRE", f"status:{agent}", 10)
    for ev in events[-8:]:
        redis.cmd("LPUSH", f"activity:{agent}", json.dumps(ev))
        redis.cmd("LTRIM", f"activity:{agent}", 0, 19)
    return status


def reporter_loop():
    while True:
        for agent, (name, port) in AGENTS.items():
            try:
                poll_agent(agent, port)
            except Exception:
                pass
        time.sleep(POLL_INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send_json(self, obj):
        payload = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _build_run(self, project_name):
        """Run-supervision view: a run == a Linear Project."""
        issues = []
        if linear.configured and project_name:
            proj = linear.project_issues(project_name)
            if proj:
                for i in (proj.get("issues") or {}).get("nodes", []):
                    issues.append({
                        "identifier": i.get("identifier"),
                        "title": i.get("title"),
                        "state": (i.get("state") or {}).get("name"),
                        "assignee": (i.get("assignee") or {}).get("name"),
                    })
        agents = []
        for agent in AGENTS:
            raw = redis.cmd("GET", f"status:{agent}")
            agents.append(json.loads(raw) if raw else {"agent": agent, "state": "down"})
        bus = []
        evs = redis.cmd("LRANGE", "bus:events", 0, 99) or []
        for e in evs:
            try:
                d = json.loads(e)
                if d.get("action") in ("task.started", "task.finished", "task.stale"):
                    bus.append(d)
            except Exception:
                pass
        return {"project": project_name, "issues": issues,
                "agents": agents, "bus": bus}

    def do_GET(self):
        if self.path == "/api/status":
            body = []
            for agent in AGENTS:
                raw = redis.cmd("GET", f"status:{agent}")
                if raw:
                    body.append(json.loads(raw))
            # recent activity across all agents
            activity = []
            for agent in AGENTS:
                evs = redis.cmd("LRANGE", f"activity:{agent}", 0, 7) or []
                for e in evs:
                    try:
                        d = json.loads(e)
                        d["agent"] = agent
                        activity.append(d)
                    except Exception:
                        pass
            activity.sort(key=lambda x: x.get("ts", ""), reverse=True)
            payload = json.dumps({"agents": body, "activity": activity[:20]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/api/projects":
            try:
                projects = linear.projects() if linear.configured else []
            except Exception as e:
                projects = []
            self._send_json({"projects": projects})
            return
        if self.path.startswith("/api/run"):
            # ?project=<name> (URL-encoded). A "run" is a Linear Project.
            from urllib.parse import urlparse, parse_qs, unquote
            qs = parse_qs(urlparse(self.path).query)
            name = unquote((qs.get("project") or [""])[0])
            self._send_json(self._build_run(name))
            return
        if self.path in ("/", "/index.html"):
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            with open(p, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_response(404)
        self.end_headers()


def main():
    threading.Thread(target=reporter_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Dev Crew dashboard: http://localhost:{PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
