# Quick Start

## Path 1: one-command local demo

Requirements:

- Python 3.11+;
- `uv` recommended; and
- port `8103` available.

```bash
./scripts/demo.sh
```

Then open `http://127.0.0.1:8103`.

The command creates or updates a local environment, starts the FastAPI service,
creates `data/conversation_success_coach.db`, and seeds the meeting-ready demo.
It does not request credentials or contact an external model API.

To use another host interface while preserving the standard port:

```bash
CSC_HOST=0.0.0.0 ./scripts/demo.sh
```

Do not expose the unauthenticated local demo to an untrusted network.

## Path 2: Docker Compose

```bash
docker compose up --build
```

Open `http://127.0.0.1:8103`.

The Compose profile:

- runs as a non-root user;
- drops Linux capabilities;
- uses a read-only root filesystem;
- writes only to the named SQLite volume; and
- includes a local health check.

Stop it with:

```bash
docker compose down
```

Remove the local demo database volume only when you intentionally want a clean
state:

```bash
docker compose down --volumes
```

## Suggested five-minute walkthrough

1. Open **Overview** and explain that the KPIs come from the real seeded API.
2. Open **Live workspace** and select **Bluebird export incident**.
3. Point out the unanswered timing/ownership question and escalation signal.
4. Click **Analyze now**.
5. Open **Suggestions** and use **Use as draft** or **Not useful**.
6. Open **Outcomes & feedback** and record a neutral outcome.
7. Open **Privacy & safety** to show no auto-send, no inference/diagnosis, and
   bounded retention.
8. Open **Audit history** to show content-minimized evidence.
9. Click **Reset demo** to restore the canonical four-scenario state.
10. Open **Architecture** and play the analysis or privacy journey.

The dashboard also includes an interactive guided tour that performs this
sequence visually.

## Seeded scenarios

| Mode | Scenario | Main coaching signal |
|---|---|---|
| Sales | Northstar analytics discovery | Migration answered; pricing remains open |
| Support | Bluebird export incident | Deadline impact, ownership, and update timing |
| Recruiting | Harborline engineering screen | Timeline answered; remote policy remains open |
| Community | Cedar Commons heated thread | Personal attack, repeated tagging, unclear rule |

All names, organizations, ids, messages, feedback, and outcomes are fictional.

## Test and validate

```bash
./scripts/test.sh
./scripts/validate.sh
./scripts/smoke.sh
```

`smoke.sh` uses port `8103` by default and a temporary SQLite database.

## Reset without the dashboard

```bash
uv run conversation-success-coach reset-demo
```

Or call:

```bash
curl -X POST http://127.0.0.1:8103/api/v1/demo/reset
```

## Clean non-demo content

The dashboard exposes per-conversation purge and retention controls. The API
also supports:

```bash
curl -X POST http://127.0.0.1:8103/api/v1/privacy/purge \
  -H 'Content-Type: application/json' \
  -d '{"scope":"all_non_demo","confirm":true}'
```

The canonical fictional seed remains. A content-free audit receipt records the
scope and deletion counts.

## Troubleshooting

### Port 8103 is already in use

Identify the existing local process or intentionally override the port:

```bash
CSC_PORT=8104 ./scripts/demo.sh
```

The documented and container default remains `8103`.

### The static dashboard says “Static preview”

You opened `site/dashboard.html` without the API. That is expected. Start the
local service and use `http://127.0.0.1:8103/dashboard` for stateful behavior.

### Python resolves below 3.11

Install `uv`, or point the fallback launcher at a supported interpreter:

```bash
CSC_PYTHON_BIN=/path/to/python3.12 ./scripts/demo.sh
```

### Start without the fictional seed

```bash
CSC_DEMO_SEED=false ./scripts/demo.sh
```

The dashboard starts empty. New retained conversation workspaces require
enabling raw storage and confirming bounded retention.

