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

Where `<agent>` is `developer`, `qa`, `tech-pm`, or `devops`.

## Message format

**Always** start with the Linear ticket identifier so completion hooks can bind the turn:

```
Ticket BON-15 — implement /login
Project: <Linear Project name if known>
Goal: ...
Acceptance criteria: ...
Report: comment on the ticket when done with useful detail (the runtime also posts a deterministic completion signal).
```

## Rules

- One task per message.
- Always reference the Linear ticket identifier (`Ticket <ID>`).
- Prefer tickets that are already linked to the effort's Linear Project.
- Track status after dispatch (mark the ticket assigned / in progress).
