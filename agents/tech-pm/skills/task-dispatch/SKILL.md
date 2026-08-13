---
name: task-dispatch
description: Send a task to another Dev Crew agent through their webhook door. Use when handing work from the PM to the developer or qa.
---

# Task Dispatch

To hand a task to another agent, send a message through their webhook door using the door client.

## From inside a container

```bash
python3 /opt/crew/crew-send.py <agent> "<message>" --container
```

Where `<agent>` is `developer`, `qa`, or `tech-pm`.

## Message format

Include: the ticket identifier, the goal, acceptance criteria, and what to report back.

```
Ticket BON-15 — implement /login
Goal: ...
Acceptance criteria: ...
Report: comment on the ticket when done, then move it to In Review.
```

## Rules

- One task per message.
- Always reference the Linear ticket identifier.
- Track status after dispatch (mark the ticket assigned / in progress).
