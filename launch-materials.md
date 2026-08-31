# Conversation Success Coach Launch Materials

Status: customer-review draft for the open-source v0.1 repository.

## One-line description

An open-source, human-controlled coach for clearer sales, support, recruiting,
and community conversations.

## Short description

Conversation Success Coach analyzes observable language and turn structure,
identifies open loops and escalation cues, and returns mode-aware suggestions
with evidence, confidence, limitations, and mandatory human review. The seeded
demo is deterministic, local-first, and requires no external credentials.

## Suggested announcement

We are sharing Conversation Success Coach as a fully seeded open-source
evaluation package for teams exploring explainable guidance in consequential
conversations. It includes a product site, operator dashboard, interactive
architecture, four fictional scenarios, API, tests, Docker profile, editable
diagrams, and explicit ethics and production-readiness boundaries.

The package does not send messages, infer protected traits, diagnose people, or
claim causal improvement. It is designed to make advice and limits inspectable.

## Demo talking points

1. Start with a visible open question in the Bluebird support incident.
2. Run deterministic analysis and inspect evidence and confidence.
3. Show manual-only, editable next actions.
4. Accept or reject a suggestion without sending anything.
5. Record a neutral outcome and explain the non-causal metric.
6. Show responsible-use redirection and privacy controls.
7. Inspect content-minimized audit history and reset the seed.
8. End with the current and proposed AWS architecture diagrams.

## Supportable claims

- Fully seeded local demo with no credentials or external runtime calls.
- Deterministic analysis for equal normalized input.
- Four explicit coaching modes sharing one safety and explanation core.
- Suggestions include evidence, confidence, limitations, and human-review
  flags.
- Stateless analysis by default with bounded optional persistence.
- Content-minimized audit, purge, retention, and one-click reset.
- Static published experience with fictional browser-local analysis and zero
  API or WebSocket traffic.

## Claims to avoid

- Production ready, enterprise ready, highly available, or scalable.
- Emotion, intent, personality, mental-health, or deception detection.
- Fair, unbiased, compliant, certified, or legally sufficient.
- Causal improvement in conversion, resolution, hiring, or community health.
- Complete DLP, anonymous data, tamper-proof audit, or guaranteed deletion from
  external backups.
- Safe use for employee ranking or high-impact eligibility decisions.

## Assets

- Repository: `https://github.com/hk-775/conversation-success-coach`
- Project site: `https://hk-775.github.io/conversation-success-coach/`
- Landing page: `site/index.html`
- Operator dashboard: `site/dashboard.html`
- Architecture explorer: `site/architecture.html`
- Current architecture: `site/assets/system-architecture.drawio`, `.png`
- AWS reference: `site/assets/aws-reference-architecture.drawio`, `.png`
- Presenter guide: `docs/DEMO.md`
- Publication inventory: `docs/PUBLICATION_ARTIFACTS.md`

## Pre-publication checklist

- Run validation, smoke, wheel-install, container, secret, and browser checks.
- Confirm diagram labels match the implemented code and readiness ledger.
- Confirm repository visibility, Pages source, branch protection, topics,
  license, and private vulnerability reporting.
- Test the static site at its repository subpath with the API unavailable.
- Confirm the published dashboard makes no API or WebSocket requests.
- Review accessibility, ethics, security, and announcement copy.
