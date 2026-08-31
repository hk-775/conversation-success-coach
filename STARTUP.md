# Evaluator Startup Guide

## Supported evaluation

Conversation Success Coach 0.1 is a local, fully seeded product demonstration
for explainable, human-controlled conversation coaching. Use fictional data
only. It is not a production communications, workforce-monitoring, diagnostic,
identity, or high-impact decision service.

## Prerequisites

- macOS or Linux
- Python 3.11 or newer
- `uv`
- local port `8103`

No cloud account, API key, database server, model provider, or Node package
installation is required.

## Start

```bash
./scripts/demo.sh
```

Open:

- product site: `http://127.0.0.1:8103`
- operator dashboard: `http://127.0.0.1:8103/dashboard`
- architecture explorer: `http://127.0.0.1:8103/architecture`
- OpenAPI: `http://127.0.0.1:8103/docs`

The service creates `data/conversation_success_coach.db` and loads the canonical
fictional sales, support, recruiting, and community scenarios.

## Five-minute acceptance path

1. Confirm the landing page states the human-control and data boundaries.
2. Open the dashboard and select **Bluebird export incident**.
3. Run analysis and inspect the unanswered ownership question.
4. Review evidence, confidence, limitations, and manual-only suggestions.
5. Record accepted/rejected feedback and a neutral outcome.
6. Show raw storage off, bounded retention, purge, and content-free audit.
7. Open the interactive architecture and downloadable diagrams.
8. Reset the demo to its canonical state.

## Validation

```bash
./scripts/validate.sh
./scripts/smoke.sh
node scripts/test_public_site.mjs
```

Expected baseline:

- Python 3.11 and 3.12 compatibility;
- branch coverage at or above 80%;
- Ruff, Bandit, dependency audit, package, and mirror validation;
- a real localhost API smoke test;
- Chrome coverage of the Pages base path, animation, dashboard views, seeded
  scenarios, mobile layout, and the zero-API/WebSocket publication boundary.

## Static backup

```bash
python3 -m http.server 8103 --directory site
```

Append `?public-site=true` to reproduce the exact published mode. The static
dashboard permits browser-local scenario selection and analysis, but all
state-changing controls are disabled and no API or WebSocket is opened.

## Before sharing

- do not expose the unauthenticated local service to an untrusted network;
- do not enter personal data, credentials, or confidential conversations;
- describe scores as directional language signals, not truth or emotion;
- describe outcomes as feedback, not causal impact;
- end with `docs/ETHICS.md` and `docs/PRODUCTION_READINESS.md`.
