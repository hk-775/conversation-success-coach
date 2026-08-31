# Demo Guide

## Objective

Show a complete, credible coaching workflow in five to ten minutes:

1. observe conversation health;
2. inspect the evidence;
3. receive a mode-aware next action;
4. preserve human choice;
5. record feedback and an outcome;
6. show responsible-use and privacy controls; and
7. reset to a known state.

## Start

```bash
./scripts/demo.sh
```

Open `http://127.0.0.1:8103/dashboard`.

## Recommended story: Bluebird support incident

### 1. Overview

Explain:

- the four conversations are fictional;
- the KPIs are API-backed seeded data;
- signal averages describe visible language, not employees or hidden participant
  profiles; and
- positive outcomes do not prove causal impact.

### 2. Live workspace

Select **Bluebird export incident**.

Point out:

- the participant states deadline impact and frustration;
- the operator asks for details without initially acknowledging impact;
- the participant asks when someone will own the fix; and
- the current operator response investigates but does not give an update
  checkpoint.

Click **Analyze now**.

Explain the response:

- momentum accounts for turn balance and the open loop;
- tone reflects visible frustration but does not claim emotion detection;
- empathy measures explicit acknowledgment of stated impact;
- the open question is shown with topic and confidence;
- the escalation signal recommends a review path, not an automatic punishment;
  and
- each next action includes evidence and limitations.

### 3. Suggestions

Open **Suggestions**.

Use **Use as draft** on one suggestion:

- the editable example is copied;
- accepted feedback is recorded; and
- no message is sent.

Use **Not useful** on another suggestion to show operator control.

### 4. Outcomes

Open **Outcomes & feedback** and record **Resolved**.

Return to **Overview** and show that feedback and outcome metrics changed. State
explicitly that this is directional and not causal attribution.

### 5. Privacy and safety

Open **Privacy & safety**.

Show:

- raw content storage off by default;
- 1–30 day analysis retention;
- content-free audit;
- per-conversation purge;
- retention execution;
- no manipulation;
- no protected-attribute inference;
- no diagnosis;
- no deceptive urgency;
- no dependency optimization; and
- no impersonation or auto-send.

Avoid enabling raw storage with real data during a public demo.

### 6. Audit

Open **Audit history**.

Show:

- analysis fingerprints rather than transcript text;
- feedback note presence rather than note content;
- deletion counts rather than deleted content; and
- explicit seed/reset events.

### 7. Architecture

Open `http://127.0.0.1:8103/architecture`.

Play:

- **Analyze conversation** for the request path;
- **Record feedback** for directional learning;
- **Privacy lifecycle** for stateless defaults and expiry; or
- **Reset the demo** for meeting reliability.

## Mode switches

### Sales

**Northstar analytics discovery**

Story: migration was answered, pricing was not. The coach recommends closing the
open buying question before introducing another ask and prohibits fabricated
scarcity.

### Recruiting

**Harborline engineering screen**

Story: timing was answered, remote policy was not. The coach recommends a
consistent process answer and prohibits protected-attribute inference or
diagnosis.

### Community

**Cedar Commons heated thread**

Story: a personal label and repeated tagging are visible. The coach recommends
moderating the behavior under a published norm, requesting a pause, and
preserving review or appeal.

## Guided mode

The dashboard's **Guided walkthrough** or **Start guided demo** button opens a
step-by-step overlay. It moves through:

1. scenario selection;
2. live analysis;
3. suggestion review;
4. outcome feedback;
5. privacy and safety; and
6. reset.

## Reset

Click **Reset demo**, or:

```bash
curl -X POST http://127.0.0.1:8103/api/v1/demo/reset
```

Reset removes mutable state from the configured local database and reconstructs
the canonical fictional seed.

## Offline static presentation

Serve or publish `site/`. The landing, dashboard, architecture explorer, and
downloadable diagrams mirror the served experience.

With `?public-site=true` or on GitHub Pages, the dashboard labels itself
**Published synthetic preview**. Scenario selection, navigation, the guided
tour, and synthetic analysis remain interactive entirely in the browser.
Transcript edits, suggestion feedback, outcomes, playbook mutation, privacy
mutation, purge, retention, and reset are disabled. No API or WebSocket is
opened.

Use the local service for stateful analysis and persistence.

## Demo recovery

If a walkthrough changes data unexpectedly:

```bash
uv run --locked conversation-success-coach reset-demo
```

If the service is not responding:

```bash
./scripts/smoke.sh
```

The smoke test uses port `8103` and a temporary database.
