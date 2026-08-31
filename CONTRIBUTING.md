# Contributing

Thank you for improving Conversation Success Coach.

## Principles for contributions

Changes must preserve:

- human choice and manual delivery;
- explainability and visible limitations;
- neutral support across all four modes;
- no protected-attribute inference;
- no mental-health diagnosis;
- no covert manipulation, fabricated urgency, or dependency optimization;
- data-minimized defaults; and
- fictional test and demo data.

Do not add a message-send endpoint, impersonation behavior, hidden participant
profile, employee-ranking score, or external provider call without an explicit
project governance decision and corresponding ethics, architecture, security,
and test updates.

## Development setup

```bash
uv sync --locked --extra dev
./scripts/test.sh
./scripts/validate.sh
./scripts/smoke.sh
node scripts/test_public_site.mjs
```

The standard local port is `8103`.

## Before submitting a change

1. Add or update tests.
2. Run the full test and validation scripts.
3. If served web files change, run `./scripts/sync-site.sh`.
4. Keep generated caches, local databases, secrets, binaries, and
   `node_modules` out of the change.
5. Update documentation and `CHANGELOG.md` for user-visible behavior.
6. Use only fictional names, organizations, messages, ids, and outcomes.
7. If architecture changes, update both editable draw.io sources, PNG renders,
   the architecture page, and the production-readiness ledger.

## Code style

- Python targets 3.11+ and is checked with Ruff.
- Public request schemas reject unknown fields.
- Analysis behavior should remain deterministic for equal normalized input.
- Audit details must not include transcript text or free-form feedback notes.
- Frontend code uses no build step or external CDN.
- Accessible names, keyboard behavior, focus states, and reduced-motion support
  are expected for interface changes.

## Adding an analysis rule

Document:

- the observable signal being measured;
- why the signal is relevant across the selected mode;
- likely false positives and false negatives;
- how evidence is redacted;
- confidence behavior;
- responsible-use implications; and
- deterministic tests.

Do not describe a language cue as proof of hidden intent, identity, emotion, or
diagnosis.

## Commit and review scope

Keep changes focused. Explain any data-model migration, API compatibility
impact, new dependency, or security boundary change in the pull request.
