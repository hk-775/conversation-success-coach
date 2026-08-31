# Production Readiness

## Readiness statement

Version 0.1 is suitable for local, synthetic evaluation and customer
demonstrations. It is **not ready** to process production conversations or
authorize employee, candidate, customer, or community decisions.

Status meanings:

- **Implemented** — present and covered by repository validation.
- **Partial** — useful local behavior with material production gaps.
- **Missing** — no production-capable implementation.
- **Blocked** — must be resolved before production consideration.

## Readiness ledger

| Area | Status | Current evidence | Production gap |
|---|---|---|---|
| Deterministic analysis | Implemented | Fingerprint and equal-input tests | Versioned rule migration and domain validation |
| Explainable suggestions | Implemented | Evidence, confidence, limitations, manual-only flags | Human-factors evaluation and outcome validation |
| Responsible-use redirection | Implemented locally | Policy code and tests for prohibited objectives | Adversarial evaluation and policy operations |
| Human review | Implemented in product boundary | No send transport; explicit review flags | Authenticated operator identity and approval records |
| Data minimization | Implemented locally | Stateless defaults, bounded retention, purge tests | Production classification, subject rights, backup deletion |
| Identifier redaction | Partial | Common direct-identifier pattern tests | Approved DLP, structured-field controls, false-negative review |
| Audit content minimization | Implemented locally | Metadata-only audit tests | Integrity anchoring, access controls, retention operations |
| Authentication | Missing / Blocked | None | Human and workload identity |
| Authorization | Missing / Blocked | Open local endpoints | Tenant roles, least privilege, administration, revocation |
| Tenant isolation | Missing / Blocked | One fictional local dataset | Partition keys, constraints, quotas, tests, operational review |
| Database availability | Missing | SQLite in one process | Replicated relational store, failover, pooling |
| Backup and restore | Missing / Blocked | Manual local file handling | Encrypted backups, PITR, restore and deletion drills |
| Schema migration | Missing / Blocked | Seed reset only | Forward and rollback migration tooling |
| Network controls | Partial | Loopback default and hardened Compose profile | TLS, trusted proxy, WAF/rate limits, CSRF/origin controls |
| Observability | Missing | Local process logs only | Redacted logs, metrics, traces, alarms, SLOs |
| Incident response | Missing | Documentation boundary only | Ownership, runbooks, exercises, forensic retention |
| Accessibility | Partial | Semantic pages and keyboard-oriented controls | Manual assistive-technology and contrast audit |
| Performance evidence | Missing | No load benchmark | Workload model, latency/error targets, capacity tests |
| Supply chain | Partial | Lockfile, pinned CI actions, Bandit, dependency audit, hardened image | Signed releases, SBOM, provenance, continuous image scanning |
| Security assurance | Partial | Unit controls and local threat model | Threat-led testing, penetration test, independent review |
| Legal and ethical review | Not claimed | Ethics guide and exclusions | Domain-specific privacy, employment, consumer, accessibility, and impact review |

## Blocking risks

1. Human and workload identities are unauthenticated.
2. The demo has no tenant isolation or protected role administration.
3. SQLite is a single-process store without production recovery controls.
4. Lexical safety and redaction rules are incomplete by construction.
5. Conversation scores have not been validated for causal impact or
   high-stakes use.
6. Backup, restore, migration, observability, and incident operations are not
   production tested.
7. No domain-specific accessibility, privacy, legal, or impact assessment has
   been completed.

## Suggested maturation sequence

### Phase 1 — evaluation hardening

- Add property tests, fuzzing, adversarial language suites, and fault injection.
- Establish representative latency and request-volume benchmarks.
- Complete manual accessibility and security reviews.
- Version analysis, safety, and data contracts.

### Phase 2 — authenticated service prototype

- Add human and workload identity with protected tenant roles.
- Replace SQLite with a transactional replicated store.
- Add migration, backup, restore, and deletion workflows.
- Establish content classification and approved DLP controls.

### Phase 3 — operational validation

- Implement redacted telemetry, alerting, incident response, and restore drills.
- Validate rule behavior and human factors for each intended domain.
- Pilot only with low-sensitivity, advisory workflows.
- Conduct independent privacy, security, accessibility, and impact review.

### Phase 4 — production decision

A production decision requires documented acceptance by engineering, product,
security, privacy, accessibility, legal, operations, and the accountable
business owner. Repository checks alone cannot authorize it.
