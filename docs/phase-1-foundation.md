# Phase 1 Foundation

## Milestone boundary

This milestone implements only the prerequisites needed by later assessment engines. It deliberately does not register nonfunctional commands for future phases.

## Requirements mapping

| Requirement | Implementation |
|---|---|
| Python environment | `pyproject.toml`, `.python-version`, `scripts/bootstrap.sh`, `Dockerfile` |
| CLI framework | `aegisx/cli.py`, `aegisx/commands/` using Typer and Rich |
| Configuration | `aegisx/core/config.py`, workspace `config.toml`, `AEGISX_*` overrides |
| Logging | Rotating workspace log and credential redaction in `aegisx/core/logging.py` |
| Error handling | Domain exceptions translated to concise CLI errors |
| Database | SQLAlchemy 2 models and transactional sessions; SQLite default |
| Project management | Authorized project creation and listing |
| Scope management | Domain/IP/CIDR/URL normalization, include/exclude rules, intrusive approval |
| Audit logging | Project and scope mutations recorded in `audit_logs` |
| Finding standardization | Pydantic contracts in `aegisx/core/schemas.py` |
| Diagnostics | `aegisx doctor` checks Python, configuration, workspace, and database |
| Tests | Unit, CLI integration, and scope-enforcement security suites |

## Workspace model

`aegisx init` creates:

```text
.aegisx/
├── config.toml
├── aegisx.db
├── evidence/
├── exports/
└── logs/
    └── aegisx.log   # created on the first logged command
```

Workspace discovery checks, in order:

1. Root `--home` CLI option.
2. `AEGISX_HOME` environment variable.
3. `.aegisx` in the current directory or a parent.
4. `.aegisx` under the current directory as the initialization recommendation.

Configuration environment overrides are:

- `AEGISX_DATABASE_URL`
- `AEGISX_LOG_LEVEL`
- `AEGISX_MAX_CONCURRENCY`
- `AEGISX_REQUESTS_PER_SECOND`
- `AEGISX_REDACT_SECRETS`
- `AEGISX_REQUIRE_INTRUSIVE_APPROVAL`

## Database design

The initial schema includes the requested entities:

- `users`
- `projects`
- `assets`
- `scopes`
- `scans`
- `findings`
- `evidence`
- `relationships`
- `attack_paths`
- `remediations`
- `audit_logs`

SQLite is the Phase 1 default. SQLAlchemy types and UUID strings remain portable to PostgreSQL; install the optional driver with `pip install -e '.[postgres]'` and configure a `postgresql+psycopg://...` URL. Schema migration tooling is pending and must be introduced before production upgrades; `create_all()` currently adds missing tables but does not migrate existing columns.

## Intelligence-engine integration contract

Every future engine must return `FindingRecord` objects. These enforce a unique ID, affected asset, severity, confidence, verification status, timestamp, assessment source, remediation, and integrity-addressed evidence.

The existing database entities prepare the intelligence layer without claiming that correlation is implemented:

- `Asset` provides normalized graph nodes.
- `Relationship` records observed edges and supporting summaries.
- `Finding` associates normalized observations with assets.
- `Evidence.sha256` supports evidence integrity checks.
- `AttackPath.status` separates hypotheses from future validated paths.
- `ProjectService.is_target_authorized()` is the mandatory pre-execution policy gate for future engines.

## Pending Phase 1 work

The next Phase 1 milestone should add database migrations, richer user/operator management, immutable/chained audit integrity, evidence-file storage APIs, project lifecycle commands, and automated CI. These are not represented as completed capabilities.
