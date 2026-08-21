#!/usr/bin/env python3
"""Dev Crew — deterministic task-completion watcher.

Tails each agent's gateway log and turns the gateway's own signals into
deterministic bus events + Linear side effects, per openspec/specs/task-completion:

  inbound message:  -> task.started   (binds "Ticket <ID>")
  response ready:   -> task.finished  (Linear auto-comment + state move, manager ping)
  silent > N min    -> task.stale

External side effects (Linear comments/state moves, manager webhook) are
BEST-EFFORT: a failure is logged and never crashes the watcher. The Redis bus
publish is the durable minimum signal.

Usage:  python3 dashboard/completion-watcher.py
Zero dependencies — stdlib only (runs on the host alongside the dashboard).
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime

from factorybus import Redis, Linear, publish, AGENTS_BASE, LINEAR_STATES

AGENTS = ["developer", "qa", "tech-pm", "devops"]

TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")
INBOUND_RE = re.compile(r"inbound message:")
RESPONSE_RE = re.compile(r"response ready:")
TICKET_RE = re.compile(r"Ticket\s+([A-Z]+-\d+)", re.I)
PROJECT_RE = re.compile(r"Project:\s*(.+)", re.I)
DELIVERY_RE = re.compile(r"chat=webhook:inbox:(\d+)")
MSG_RE = re.compile(r"msg='(.*?)'", re.S)
DURATION_RE = re.compile(r"time=([\d.]+)s")
API_CALLS_RE = re.compile(r"api_calls=(\d+)")
# PR hint for the "success + PR -> In Review" rule (best-effort).
PR_RE = re.compile(r"pull request|opened (a |the )?PR|PR\s*#\d+|/pull/\d+", re.I)

STALE_MINUTES = float(os.environ.get("WATCHER_STALE_MINUTES", "30"))
POLL_INTERVAL = float(os.environ.get("WATCHER_POLL_INTERVAL", "2.0"))
MANAGER_WEBHOOK_URL = os.environ.get("MANAGER_WEBHOOK_URL", "").strip()

# Agent log path: AGENTS_BASE/<agent>/hermes-home/logs/agent.log
def log_path(agent):
    return os.path.join(AGENTS_BASE, agent, "hermes-home", "logs", "agent.log")


def parse_ts(line):
    m = TS_RE.search(line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def extract_msg(line):
    m = MSG_RE.search(line)
    return m.group(1) if m else ""


class Turn:
    __slots__ = ("ticket", "project", "delivery_id", "started_ts", "started_mono",
                 "window", "stale_emitted")

    def __init__(self, line, ts):
        self.ticket = None
        self.project = None
        self.delivery_id = None
        tm = TICKET_RE.search(line)
        if tm:
            self.ticket = tm.group(1).upper()
        pm = PROJECT_RE.search(extract_msg(line))
        if pm:
            self.project = pm.group(1).strip()
        dm = DELIVERY_RE.search(line)
        if dm:
            self.delivery_id = dm.group(1)
        self.started_ts = ts
        self.started_mono = time.monotonic()
        self.window = [line]
        self.stale_emitted = False


def manager_ping(payload):
    """Best-effort POST of the structured payload to the manager webhook."""
    if not MANAGER_WEBHOOK_URL:
        return None
    try:
        req = urllib.request.Request(
            MANAGER_WEBHOOK_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"[watcher] manager ping failed: {e}")
        return None


class Watcher:
    def __init__(self):
        self.redis = Redis()
        self.linear = Linear()
        self.started = datetime.now()
        # per-agent: byte offset into the log + in-flight turn
        self.offsets = {a: None for a in AGENTS}
        self.turns = {a: None for a in AGENTS}

    def _read_new_lines(self, agent):
        path = log_path(agent)
        lines = []
        try:
            size = os.path.getsize(path)
        except OSError:
            return lines
        offset = self.offsets[agent]
        if offset is None or offset > size:
            offset = size  # first run / log rotated: start from the tail
        if offset == size:
            self.offsets[agent] = size
            return lines
        try:
            with open(path, "rb") as f:
                f.seek(offset)
                data = f.read()
                self.offsets[agent] = offset + len(data)
        except OSError:
            return lines
        text = data.decode(errors="replace")
        for raw in text.splitlines():
            if raw.strip():
                lines.append(raw)
        return lines

    def _emit_start(self, agent, turn):
        payload = {
            "agent": agent,
            "ticket": turn.ticket,
            "project": turn.project,
            "summary": extract_msg(turn.window[0])[:200],
        }
        publish(self.redis, agent, "task.started", "*", payload)
        print(f"[watcher] task.started {agent} {turn.ticket or '(no ticket)'}")
        # Best-effort: Linear In Progress + short comment (only when bound).
        if turn.ticket and self.linear.configured:
            iid = self.linear.issue_id(turn.ticket)
            if iid:
                self.linear.move_state(iid, LINEAR_STATES["in_progress"])
                self.linear.comment(
                    iid,
                    f"> *This was generated by AI.*\n\n"
                    f"{agent} started work on {turn.ticket}.",
                )

    def _emit_finish(self, agent, turn, line):
        dur_m = DURATION_RE.search(line)
        calls_m = API_CALLS_RE.search(line)
        duration_s = float(dur_m.group(1)) if dur_m else None
        api_calls = int(calls_m.group(1)) if calls_m else None
        window = "\n".join(turn.window)
        # The gateway log has no reliable abort/failure marker, so a completed
        # turn is "success"; silence is covered separately by task.stale.
        status = "success"
        payload = {
            "agent": agent,
            "ticket": turn.ticket,
            "status": status,
            "summary": extract_msg(turn.window[0])[:200],
            "duration_s": duration_s,
            "api_calls": api_calls,
            "project": turn.project,
        }
        publish(self.redis, agent, "task.finished", "*", payload)
        print(f"[watcher] task.finished {agent} {turn.ticket or '(no ticket)'} "
              f"{status} ({duration_s}s, {api_calls} calls)")

        has_pr = bool(PR_RE.search(window))
        if turn.ticket and self.linear.configured:
            iid = self.linear.issue_id(turn.ticket)
            if iid:
                # State rule: success + PR -> In Review; success -> Done;
                # failure/blocked -> Blocked (team BON has none -> no move).
                target = LINEAR_STATES["in_review"] if has_pr else LINEAR_STATES["done"]
                self.linear.move_state(iid, target)
                body = (
                    f"> *This was generated by AI.*\n\n"
                    f"**{agent}** finished **{turn.ticket}** ({status}).\n"
                )
                if duration_s is not None:
                    body += f"Duration: {duration_s:.0f}s, {api_calls} API calls.\n"
                if has_pr:
                    body += "A PR/reviewable artifact was detected -> In Review.\n"
                self.linear.comment(iid, body)

        manager_ping(payload)

    def _emit_stale(self, agent, turn):
        payload = {
            "agent": agent,
            "ticket": turn.ticket,
            "status": "stale",
            "summary": extract_msg(turn.window[0])[:200],
            "silent_seconds": int(time.monotonic() - turn.started_mono),
        }
        publish(self.redis, agent, "task.stale", "*", payload)
        turn.stale_emitted = True
        print(f"[watcher] task.stale {agent} {turn.ticket or '(no ticket)'}")

    def poll_agent(self, agent):
        for line in self._read_new_lines(agent):
            ts = parse_ts(line)
            if ts and ts < self.started:
                continue  # skip historical lines (first run / rotation)
            if INBOUND_RE.search(line):
                if self.turns[agent] is not None:
                    # An inbound without a matching response: flush the old turn
                    # as finished-without-response (keeps the bus consistent).
                    self._emit_finish(agent, self.turns[agent],
                                      f"time=0s api_calls=0")
                self.turns[agent] = Turn(line, ts)
                self._emit_start(agent, self.turns[agent])
                continue
            if RESPONSE_RE.search(line):
                turn = self.turns[agent]
                if turn is not None:
                    # The webhook door processes one turn at a time, so any
                    # "response ready" finalizes the in-flight turn.
                    self._emit_finish(agent, turn, line)
                    self.turns[agent] = None
                continue
            if self.turns[agent] is not None:
                self.turns[agent].window.append(line)

        # Stale check for the in-flight turn.
        turn = self.turns[agent]
        if turn is not None and not turn.stale_emitted:
            if time.monotonic() - turn.started_mono > STALE_MINUTES * 60:
                self._emit_stale(agent, turn)

    def run(self):
        print(f"[watcher] started, agents={AGENTS}, stale={STALE_MINUTES}min, "
              f"manager_ping={'on' if MANAGER_WEBHOOK_URL else 'off'}")
        while True:
            for agent in AGENTS:
                try:
                    self.poll_agent(agent)
                except Exception as e:  # never let the watcher die
                    print(f"[watcher] error polling {agent}: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    Watcher().run()
