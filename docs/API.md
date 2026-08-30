# API Reference

Base URL for the local demo:

```text
http://127.0.0.1:8103/api/v1
```

Interactive OpenAPI documentation:

```text
http://127.0.0.1:8103/docs
```

All request models reject unknown fields. API responses are sent with
`Cache-Control: no-store`.

## Errors

Validation errors use:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request did not match the API contract.",
    "issues": [
      {
        "field": "body.turns",
        "message": "List should have at least 1 item after validation, not 0",
        "type": "too_short"
      }
    ]
  }
}
```

Endpoint errors use FastAPI's `detail` envelope with a structured code and
message where applicable.

## Modes and roles

Modes:

```text
sales | support | recruiting | community
```

Turn roles:

```text
operator | participant | observer
```

## `GET /health`

Returns service posture:

```json
{
  "status": "ok",
  "service": "conversation-success-coach",
  "version": "0.1.0",
  "engine": "local-deterministic",
  "external_network_calls": false,
  "message_delivery_capability": false,
  "demo_seed": true,
  "seed_version": "2026-08-30.1"
}
```

## `GET /responsible-use`

Returns the human-agency, prohibited-capability, and data-default summary.

## Conversations

### `GET /conversations`

Optional query:

- `mode=sales|support|recruiting|community`

Returns summaries and the latest persisted analysis.

### `POST /conversations`

Creates a retained non-demo workspace. Raw storage must first be enabled with
`PUT /privacy/settings`.

```json
{
  "title": "Fictional service review",
  "mode": "support",
  "owner": "Taylor Quill",
  "participant_label": "Case participant",
  "goal": "Resolve a fictional issue.",
  "stage": "Intake",
  "retention_days": 7,
  "consent_confirmed": true
}
```

### `GET /conversations/{conversation_id}`

Returns conversation metadata, ordered turns, and latest persisted analysis.

### `POST /conversations/{conversation_id}/turns`

Adds a turn to a retained local transcript:

```json
{
  "speaker": "Case participant",
  "role": "participant",
  "text": "When will the next update arrive?",
  "timestamp": null
}
```

The endpoint stores locally; it does not send the turn.

## Coaching

### `POST /analyze`

Request:

```json
{
  "mode": "support",
  "conversation_id": "conv_support_bluebird",
  "turns": [
    {
      "speaker": "Rowan Hart",
      "role": "participant",
      "text": "This is blocking our deadline. When will someone own the fix?",
      "timestamp": "2026-08-30T12:00:00Z"
    },
    {
      "speaker": "Imani Cole",
      "role": "operator",
      "text": "I can see the prior ticket and I am checking the worker.",
      "timestamp": "2026-08-30T12:07:00Z"
    }
  ],
  "context": {
    "goal": "Restore access and establish an update cadence.",
    "stage": "Escalated investigation",
    "known_facts": []
  },
  "data_handling": {
    "persist_analysis": true,
    "store_raw_content": false,
    "retention_days": 7,
    "consent_confirmed": false
  }
}
```

Limits:

- 1–80 turns;
- speaker up to 80 characters;
- turn text up to 4,000 characters;
- goal up to 500 characters;
- up to 20 known facts;
- persistence retention 1–30 days; and
- raw storage requires persistence, consent, an existing conversation, and the
  operator-level setting.

Response fields:

- `analysis_id`
- `conversation_id`
- `mode`
- deterministic `fingerprint`
- `created_at`
- `overall_score`
- `status`
- `signals`
- `unanswered_questions`
- `risks`
- `suggestions`
- `responsible_use`
- `limitations`
- `persisted`
- `expires_at`

Every suggestion contains:

```json
{
  "id": "sug_...",
  "category": "answer_open_question",
  "priority": "now",
  "title": "Answer the open loop directly",
  "action": "Address the outstanding question before introducing a new ask.",
  "example_language": "Draft to adapt: ...",
  "rationale": "Direct answers reduce avoidable friction.",
  "evidence": ["When will someone own the fix?"],
  "confidence": 0.84,
  "limitations": ["..."],
  "playbook_refs": ["pb_support_recovery"],
  "requires_human_review": true,
  "delivery": "manual_only",
  "can_auto_send": false
}
```

### `POST /suggestions`

Uses the same request fields as `/analyze` plus:

```json
{"max_suggestions": 3}
```

Range: 1–5.

It returns the selected suggestions, responsible-use decision, and limitations.
If persistence is requested, it uses the same storage path as `/analyze`.

## Feedback

### `POST /feedback`

Accepted:

```json
{
  "kind": "accepted",
  "suggestion_id": "sug_...",
  "note": "Useful after editing."
}
```

Rejected:

```json
{
  "kind": "rejected",
  "suggestion_id": "sug_...",
  "note": ""
}
```

Outcome:

```json
{
  "kind": "outcome",
  "conversation_id": "conv_support_bluebird",
  "outcome": "resolved",
  "note": "Fictional outcome."
}
```

Outcomes:

```text
advanced | resolved | no_change | escalated | declined
```

Free-form notes are stored in the feedback record but excluded from audit
details.

### `GET /feedback`

Query:

- `limit` from 1 through 500.

## Playbooks

### `GET /playbooks`

Queries:

- optional `mode`;
- optional `enabled_only=true|false`.

### `POST /playbooks`

```json
{
  "name": "Clear checkpoints",
  "mode": "support",
  "description": "Make ownership and timing explicit.",
  "principles": [
    "Name one owner.",
    "Give one realistic update checkpoint."
  ],
  "enabled": true
}
```

### `PATCH /playbooks/{playbook_id}`

Supports partial updates to:

- `name`
- `description`
- `principles`
- `enabled`

### `DELETE /playbooks/{playbook_id}`

Returns `204 No Content`.

## Metrics and audit

### `GET /metrics`

Optional `mode` query.

Returns:

- conversation and analysis counts;
- suggestion counts;
- accepted and rejected counts;
- acceptance rate;
- outcome and positive-outcome counts;
- at-risk latest-analysis count;
- average observable signals;
- mode breakdown; and
- interpretation limitations.

### `GET /audit`

Queries:

- optional exact `event_type`;
- `limit` from 1 through 500.

Each item includes `content_minimized=true`.

## Privacy

### `GET /privacy/settings`

Returns:

- raw-content setting;
- default analysis retention;
- audit retention;
- update time; and
- immutable data defaults.

### `PUT /privacy/settings`

```json
{
  "allow_raw_content_storage": false,
  "default_analysis_retention_days": 7,
  "audit_retention_days": 30
}
```

### `POST /privacy/purge`

Conversation:

```json
{
  "scope": "conversation",
  "conversation_id": "conv_...",
  "confirm": true
}
```

Expired:

```json
{
  "scope": "expired",
  "confirm": true
}
```

All non-demo:

```json
{
  "scope": "all_non_demo",
  "confirm": true
}
```

The response includes deletion counts and confirms that the retained audit does
not contain transcript text.

### `POST /privacy/retention/run`

Applies configured analysis, conversation, and audit expiry.

## Demo

### `POST /demo/reset`

Restores the canonical four fictional scenarios and playbooks. Existing mutable
demo and non-demo state in the configured database is removed.

The endpoint is intentionally destructive within the local product database and
should not be exposed as-is in a production service.

