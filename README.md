# Conversation Success Coach

Conversation Success Coach is an open-source, human-in-control coaching system
for consequential conversations. It analyzes observable conversation patterns,
explains what it found, and suggests editable next-best actions for:

- sales;
- customer support;
- recruiting; and
- community moderation.

It runs locally with a real FastAPI service, SQLite state, four fictional seeded
scenarios, a responsive operator dashboard, and an animated architecture
explorer. It makes no external model or network calls and requires no
credentials.

## Start the seeded demo

Prerequisites: Python 3.11+ and either
[uv](https://docs.astral.sh/uv/) or an environment with FastAPI and Uvicorn.

```bash
./scripts/demo.sh
```

Open:

- product home: `http://127.0.0.1:8103`
- dashboard: `http://127.0.0.1:8103/dashboard`
- architecture: `http://127.0.0.1:8103/architecture`
- OpenAPI UI: `http://127.0.0.1:8103/docs`

The first launch seeds sales, support, recruiting, and community scenarios,
their analyses, playbooks, feedback, outcomes, and content-minimized audit
history.

Docker is also one command:

```bash
docker compose up --build
```

See [QUICKSTART.md](QUICKSTART.md) for the complete walkthrough.

## What the coach analyzes

Each response includes:

- **momentum** — turn balance, forward-motion cues, stalling language, and open
  loops;
- **tone** — observable courtesy, friction, emphasis, and hostile-language cues;
- **unanswered questions** — topic-aware detection for pricing, timing,
  implementation, policy, remote/location, remedy, and privacy questions;
- **clarity** — sentence structure, vague qualifiers, and concrete time or
  quantity cues;
- **empathy** — explicit acknowledgment of stated impact, without claiming to
  know hidden emotion;
- **risk and escalation** — threats, harassment, trust breaks, and obvious
  sensitive-data shapes; and
- **next-best actions** — mode-specific, editable suggestions with rationale,
  evidence, confidence, limitations, and playbook references.

Equal normalized inputs produce equal fingerprints, scores, and suggestions.
The engine is deterministic Python code, not a remote model wrapper.

## Product experience

The operator dashboard includes:

- overview KPIs and average signals;
- a live conversation workspace;
- suggestion acceptance and rejection;
- neutral outcome feedback;
- mode-scoped playbooks;
- privacy and retention controls;
- content-minimized audit history;
- a guided meeting walkthrough; and
- one-click demo reset.

The `site/` directory is an exact static mirror of the served landing,
dashboard, architecture, and assets. When published without the API, the
dashboard automatically becomes a clearly labeled static preview.

## Human agency and responsible use

Conversation Success Coach provides suggestions only.

- It has no message-send endpoint or delivery transport.
- It never impersonates an operator.
- Every suggestion is marked `manual_only`, `requires_human_review=true`, and
  `can_auto_send=false`.
- It does not infer protected attributes.
- It does not diagnose mental health or personality.
- It does not help fabricate deadlines, scarcity, or urgency.
- It does not optimize for dependency or covert manipulation.

Explicit unsafe objectives are returned as a responsible-use redirection with a
transparent alternative. See [docs/ETHICS.md](docs/ETHICS.md).

## Data minimization

Ad hoc analysis defaults to no persistence. Persisted analyses require an
explicit 1–30 day retention period. Raw conversation storage additionally
requires:

1. the operator-level raw-storage setting;
2. request-level consent confirmation; and
3. a bounded conversation expiry.

Audit events contain state metadata and counts, not transcript text or feedback
note contents. Common direct-identifier shapes are redacted from evidence
excerpts. Privacy APIs support per-conversation purge, all-non-demo purge, and
retention enforcement.

## API example

```bash
curl -s http://127.0.0.1:8103/api/v1/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "support",
    "turns": [
      {
        "speaker": "Case participant",
        "role": "participant",
        "text": "This is blocking our deadline. When will it be fixed?"
      },
      {
        "speaker": "Case operator",
        "role": "operator",
        "text": "I am checking the worker now."
      }
    ]
  }'
```

Important response fields:

```json
{
  "overall_score": 54,
  "status": "watch",
  "signals": {
    "momentum": {"score": 60, "label": "steady", "confidence": 0.55},
    "tone": {"score": 52, "label": "strained", "confidence": 0.52},
    "clarity": {"score": 78, "label": "crisp", "confidence": 0.5},
    "empathy": {"score": 34, "label": "missing", "confidence": 0.5}
  },
  "suggestions": [
    {
      "title": "Answer the open loop directly",
      "delivery": "manual_only",
      "requires_human_review": true,
      "can_auto_send": false
    }
  ]
}
```

See [docs/API.md](docs/API.md) for every endpoint and schema behavior.

## Architecture

```text
Static browser UI
        │
        ▼
Validated FastAPI contracts
        │
        ├── Responsible-use policy
        ├── Deterministic signal analyzers
        ├── Mode-specific coaching adapters
        └── Explanation and limitation builder
        │
        ▼
Human review ───── optional bounded persistence ─────► SQLite
```

The service, engine, repository, seed, and static experience are intentionally
compact enough to inspect in one sitting. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API surface

| Area | Endpoints |
|---|---|
| System | `GET /api/v1/health`, `GET /api/v1/responsible-use` |
| Conversations | `GET/POST /api/v1/conversations`, `GET /api/v1/conversations/{id}`, `POST /api/v1/conversations/{id}/turns` |
| Coaching | `POST /api/v1/analyze`, `POST /api/v1/suggestions` |
| Feedback | `GET/POST /api/v1/feedback` |
| Playbooks | `GET/POST /api/v1/playbooks`, `PATCH/DELETE /api/v1/playbooks/{id}` |
| Observability | `GET /api/v1/metrics`, `GET /api/v1/audit` |
| Privacy | `GET/PUT /api/v1/privacy/settings`, `POST /api/v1/privacy/purge`, `POST /api/v1/privacy/retention/run` |
| Demo | `POST /api/v1/demo/reset` |

## Development

```bash
./scripts/test.sh
./scripts/validate.sh
./scripts/smoke.sh
```

The smoke test starts the real product on the standard demo port, `8103`, and
checks health, all three pages, seeded state, analysis, and manual-only
suggestion flags.

Project structure:

```text
src/conversation_success_coach/
  analysis.py       deterministic signal and suggestion engine
  safety.py         responsible-use policy and evidence redaction
  schemas.py        strict public contracts
  repository.py     SQLite state, metrics, audit, purge, retention
  seed.py           canonical fictional demo
  app.py            FastAPI application and pages
  web/              served landing, dashboard, architecture, assets
site/               exact publishable static mirror of web/
tests/              mode, safety, determinism, state, feedback, privacy tests
docs/               architecture, ethics, API, demo, deployment
```

## Limitations

- Language analysis is heuristic and English-oriented.
- It can miss irony, organizational context, policy nuance, and power dynamics.
- It does not transcribe calls or integrate with email, CRM, ticketing, ATS, or
  community platforms.
- The local demo has no authentication or multi-tenant authorization. Do not
  expose it directly to an untrusted network.
- SQLite is appropriate for this standalone demo, not a high-write distributed
  deployment.
- Feedback and outcomes are directional; they do not establish causal impact.

## License and conduct

Licensed under [MIT-0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md),
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md), and
[NOTICE](NOTICE).

