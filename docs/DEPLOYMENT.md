# Deployment

## Supported profile: local evaluation

The complete supported profile is a local or single-host evaluation:

- FastAPI and static assets in one process;
- SQLite on a local path or named volume;
- fictional seed enabled; and
- loopback binding on port `8103`.

```bash
./scripts/demo.sh
```

The supported installer and runner is `uv`; commands use `uv.lock`.

## Docker Compose

```bash
docker compose up --build
```

Default URL:

```text
http://127.0.0.1:8103
```

The container:

- uses Python 3.12;
- runs as a non-root `coach` user;
- exposes container port `8103`;
- drops all Linux capabilities;
- sets `no-new-privileges`;
- uses a read-only root filesystem;
- uses `/tmp` as a bounded tmpfs;
- writes SQLite state to `/data`; and
- uses a standard-library health check.

The host port can be overridden with `CSC_PORT`, but `8103` remains the standard
demo and container port.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `CSC_HOST` | `127.0.0.1` | Bind interface |
| `CSC_BIND_ADDRESS` | `127.0.0.1` | Compose host-side bind address |
| `CSC_PORT` | `8103` | Local/demo port |
| `CSC_DATABASE_PATH` | `data/conversation_success_coach.db` | SQLite path |
| `CSC_DEMO_SEED` | `true` | Seed fictional demo state |
| `CSC_DOCS_ENABLED` | `true` | Serve OpenAPI and ReDoc pages |

There are intentionally no model-provider keys or outbound endpoint variables.

## Static site

`site/` is an exact mirror of:

```text
src/conversation_success_coach/web/
```

Update it with:

```bash
./scripts/sync-site.sh
```

Validate equality with:

```bash
./scripts/validate.sh
```

The static dashboard enters a clearly labeled published mode on GitHub Pages or
with `?public-site=true`. It supports browser-local scenario exploration and
synthetic analysis, disables state-changing controls, and makes no API,
external HTTP, or WebSocket request.

## Proposed AWS reference

`site/assets/aws-reference-architecture.png` and its editable draw.io source
show a possible production direction:

- CloudFront with WAF;
- S3 through Origin Access Control for static assets;
- a CloudFront VPC origin to an internal ALB;
- Cognito for human authentication;
- ECS Fargate in private multi-AZ subnets;
- RDS for PostgreSQL Multi-AZ;
- Secrets Manager, KMS, EventBridge Scheduler, CloudWatch, ECR, and GitHub
  Actions OIDC.

This repository does not deploy that topology and includes no infrastructure
templates. Treat the diagram as an architecture discussion artifact only.

## Production gap

The package is not a production multi-user service as shipped.

Before network exposure, add:

### Identity and authorization

- authenticated operators;
- tenant and workspace isolation;
- role-based access for purge, settings, playbooks, audit, and reset;
- session protection; and
- an emergency access revocation process.

### Network and HTTP controls

- TLS;
- trusted proxy and host configuration;
- CSRF controls if using cookies;
- origin allowlists;
- request-body limits;
- rate limits;
- timeouts;
- abuse monitoring; and
- OpenAPI access controls.

### Data protection

- an approved data classification;
- encryption and key management appropriate to the platform;
- backup, restore, and tested deletion behavior;
- a production-grade DLP layer if sensitive content is allowed;
- tenant-scoped retention policy;
- backup deletion semantics;
- legal and regulatory review; and
- auditable administrator access.

### Persistence and scale

SQLite is a single-host store. For multiple service replicas or substantial
write concurrency, move the repository contract to a production database with:

- migrations;
- transaction isolation review;
- connection pooling;
- high availability;
- backup and point-in-time recovery;
- tenant constraints;
- deletion jobs; and
- metrics for retention failures.

### Operational controls

- structured service logging that preserves content minimization;
- health, readiness, and dependency checks;
- service and database metrics;
- alerts;
- vulnerability management;
- dependency locks;
- signed images and releases;
- software bill of materials;
- incident response;
- disaster recovery; and
- change review for responsible-use policy.

## Authentication boundary warning

`POST /api/v1/demo/reset`, privacy settings, purge, playbook mutation, and audit
access are intentionally open in the local demo. They must be administrator
operations in any shared deployment.

## External integrations

The current product does not connect to CRM, support, ATS, community, email,
chat, or telephony systems.

If a future integration imports conversation content:

- obtain appropriate authorization and consent;
- minimize fields before transfer;
- preserve source timestamps and speaker roles without inferring identity;
- bound retention;
- prevent accidental ingestion of credentials;
- keep sending outside this coaching service; and
- maintain an explicit human review step.

## Smoke test

```bash
./scripts/smoke.sh
```

The script:

1. creates a temporary SQLite directory;
2. starts the product on `127.0.0.1:8103`;
3. waits for health;
4. checks landing, dashboard, architecture, and seeded conversations;
5. posts a real analysis request;
6. verifies manual-only and no-auto-send response flags; and
7. stops the service and removes the temporary directory.
