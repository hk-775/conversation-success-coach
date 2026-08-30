# Security Policy

## Supported versions

The project is pre-1.0. Security fixes are applied to the latest release on the
main development branch.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, sensitive
conversation content, or personal data. Contact the project maintainer through
the private security-reporting channel associated with the repository where
this package is hosted.

Include:

- affected version or commit;
- affected endpoint or component;
- reproduction steps using fictional data;
- impact;
- any suggested mitigation; and
- whether the report contains sensitive details.

Expect an acknowledgement within five business days when a maintainer contact
channel is available.

## Local demo security boundary

The shipped local demo:

- has no authentication or tenant isolation;
- is intended to bind to `127.0.0.1`;
- stores SQLite state on local disk;
- exposes interactive OpenAPI documentation by default;
- performs no external provider calls; and
- has no message-delivery capability.

Do not bind it to a public or untrusted network without adding:

- authentication and role-based authorization;
- TLS at a trusted reverse proxy;
- CSRF controls if cookie authentication is introduced;
- origin and host allowlists;
- rate and request-size limits;
- encrypted backups and platform-specific disk protection;
- production database concurrency and recovery controls; and
- monitoring, patching, and incident-response procedures.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Data handling

- Use fictional data in reports and tests.
- Do not submit real conversation content to public issues.
- Audit events are designed not to contain transcript text.
- Evidence excerpts redact common direct-identifier shapes, but this is
  heuristic and not a complete data-loss-prevention system.
- Purge APIs remove retained content but cannot erase copies exported or backed
  up outside this application.

## Dependency and supply-chain practices

CI tests Python 3.11 and 3.12, runs Ruff and pytest, validates the static mirror,
and performs a localhost smoke test on port `8103`. Before a production release,
maintainers should additionally produce a locked dependency set, dependency
audit, container vulnerability scan, signed release artifact, and software bill
of materials.

