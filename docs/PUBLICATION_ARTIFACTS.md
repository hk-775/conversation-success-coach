# Publication Artifacts

## Purpose

This inventory keeps the repository, packaged web experience, static site,
architecture material, evaluator guidance, and release checks aligned.

## Customer-facing set

| Artifact | Purpose | Canonical source |
|---|---|---|
| Repository overview | Product boundary, demo, controls, limitations, document index | `README.md` |
| Quick evaluation | Installation and first walkthrough | `QUICKSTART.md` |
| Evaluator startup | Acceptance checks, static backup, sharing cautions | `STARTUP.md` |
| Product site | Public framing and enforced boundaries | `site/index.html` |
| Operator dashboard | Seeded scenarios, analysis, feedback, privacy, audit | `site/dashboard.html` |
| Architecture explorer | Interactive implemented flows and downloadable diagrams | `site/architecture.html` |
| Current architecture | Implemented process and trust boundary | `site/assets/system-architecture.drawio`, `.png` |
| AWS reference | Proposed production deployment, clearly labeled | `site/assets/aws-reference-architecture.drawio`, `.png` |
| Long-form architecture | Components, flows, lifecycle, persistence | `docs/ARCHITECTURE.md` |
| API reference | Endpoints and data contracts | `docs/API.md` |
| Demo guide | Five-to-ten-minute presenter path | `docs/DEMO.md` |
| Ethics | Enforced controls, residual risk, excluded uses | `docs/ETHICS.md` |
| Threat model | Assets, actors, threats, controls, residual risks | `docs/THREAT_MODEL.md` |
| Production readiness | Evidence, blockers, maturation sequence | `docs/PRODUCTION_READINESS.md` |
| Deployment | Local/Docker profiles and proposed AWS direction | `docs/DEPLOYMENT.md` |
| Launch materials | Supportable claims, claims to avoid, asset locations | `launch-materials.md` |

## Visual source of truth

- `system-architecture.drawio` is the editable current-system diagram.
- `system-architecture.png` is the README and presentation render.
- `aws-reference-architecture.drawio` is the editable proposed deployment.
- `aws-reference-architecture.png` is its presentation render.

The four files exist under both the packaged web assets and `site/assets/`.
`scripts/validate_package.py` requires exact byte equality.

## Static publication

The Pages workflow publishes only `site/`. It contains no credentials,
telemetry, remote fonts, third-party scripts, or network API dependency. The
GitHub Pages host enters fictional read-only mode before any API call. Scenario
selection, navigation, architecture animation, and synthetic analysis work;
state-changing controls remain disabled.

The workflow installs the locked `uv` environment, validates the package
mirror, and runs Chrome against the repository Pages base before upload.

## Validation

```bash
./scripts/validate.sh
./scripts/smoke.sh
node scripts/test_public_site.mjs
```

Then inspect `/`, `/dashboard.html`, and `/architecture.html` from `site/`.
Use `?public-site=true` for the exact no-API publication behavior.

## Intentional omissions

Version 0.1 does not publish cloud templates, a production identity system,
production dashboards, benchmark claims, real customer data, trained models,
third-party connectors, or signed runtime artifacts. Publishing those would
imply an operational surface or assurance level that does not exist.
