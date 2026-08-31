# Threat Model

## Scope

This model covers the local v0.1 FastAPI service, deterministic coaching
engine, responsible-use gate, SQLite state, static pages, and seeded demo.

## Assets

- Conversation content voluntarily supplied for analysis.
- Derived signals, risks, suggestions, explanations, and fingerprints.
- Privacy settings, retention periods, purge receipts, and audit metadata.
- Playbooks and operator feedback.
- Human agency: the requirement that suggestions remain optional and manual.
- Availability and integrity of the canonical fictional demo.

## Actors

- Human operator reviewing coaching suggestions.
- Local API client submitting explicit conversation turns.
- Local evaluator controlling the host.
- Malicious client attempting malformed, abusive, or privacy-invasive input.
- Local process or administrator with filesystem access.
- Contributor proposing source changes.

## Trust assumptions

- The local evaluator protects the host account and SQLite file.
- The caller has authority to submit the supplied fictional or approved
  conversation content.
- Caller-provided role, consent, and retention assertions are truthful.
- Cooperative writers use the application service.
- Python, SQLite, FastAPI, and the operating system behave as documented.

Identity, authority, consent, and content classification are major evaluation
assumptions.

## Threats and controls

### Automatic persuasion or impersonation

Controls: no delivery endpoint or transport, manual-only response fields,
visible draft labeling, human-review requirements, and tests.

Residual risk: an external client can copy text into another system and misuse
it outside this product.

### Manipulative or discriminatory objective

Controls: explicit responsible-use rules redirect covert manipulation,
protected-trait inference, diagnosis, fake urgency, dependency goals,
impersonation, and automatic sending.

Residual risk: lexical rules can be evaded or a benign label can conceal a
harmful organizational objective.

### Sensitive content is retained unexpectedly

Controls: ad hoc analysis is stateless by default; persistence requires bounded
retention; raw storage additionally requires an operator setting, consent, and
an existing workspace.

Residual risk: operator assertions are not independently verified, and local
database or backup copies remain accessible to the host administrator.

### Sensitive identifiers leak through evidence or audit

Controls: common email, phone, payment-number, government-id, and long-number
shapes are redacted from evidence; audit excludes transcript and free-form note
contents.

Residual risk: pattern redaction is not complete DLP and contextual identifiers
can remain.

### Unauthorized mutation, purge, or reset

Controls: loopback binding by default and explicit confirmation fields for
destructive API operations.

Residual risk: there is no authentication, authorization, CSRF protection, or
tenant isolation. Any process able to reach the local service can use open
endpoints.

### Cross-tenant disclosure

Controls: none are claimed; the shipped package is a single local fictional
dataset.

Residual risk: production multi-tenancy is blocked until tenant keys,
authorization, database constraints, quotas, and isolation tests exist.

### Analysis is treated as truth

Controls: directional labels, evidence, confidence, limitations, ethics
documentation, and explicit statements that scores do not reveal emotion,
intent, identity, or causality.

Residual risk: operators can over-trust a score or use it for worker ranking
despite the stated boundary.

### Denial of service

Controls: strict request models, bounded text and collection lengths,
loopback-only default binding, and container resource-hardening defaults.

Residual risk: no production rate limiting, queue isolation, load testing, or
storage quota exists.

### Browser or static-asset compromise

Controls: repository-owned assets, no third-party runtime scripts or fonts,
escaped dynamic text, fictional fallback data, and a Chrome test that rejects
API, external HTTP, and WebSocket traffic in published mode.

Residual risk: repository or hosting compromise can alter static assets; the
local demo is not authenticated.

### Dependency or CI compromise

Controls: locked dependencies, immutable action SHAs, minimal runtime
dependencies, Bandit, dependency audit, wheel verification, and a pinned
hardened container base.

Residual risk: releases are not signed, no SBOM or provenance attestation is
published, and image scanning is not continuous.

## Out of scope

- Compromised host administrator, Python runtime, browser, or kernel.
- Independent truth of caller consent or authority.
- Complete prevention of data exfiltration from copied output.
- Legal or regulatory sufficiency.
- Employee ranking or high-impact eligibility decisions.
- Production AWS resources; the AWS diagram is a proposal only.

## Required production work

See `docs/PRODUCTION_READINESS.md`, `docs/DEPLOYMENT.md`, and
`docs/ETHICS.md`.
