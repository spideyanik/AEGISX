# AEGISX

**From Isolated Vulnerability Detection to Unified Cybersecurity Intelligence.**

AEGISX is an evidence-driven CLI framework for authorized cybersecurity assessment. Development follows an incremental roadmap; this repository currently implements the **Phase 1 foundation only**.

## Project motive

> **To transform traditional isolated cybersecurity testing into an intelligent, evidence-driven, and interconnected security assessment process.**

AEGISX is designed to unify network VAPT, web application testing, API security, and AI/LLM security under a consistent project, scope, evidence, and intelligence model. Its long-term goal is not merely to collect scanner output, but to correlate findings across trust boundaries, identify evidence-supported attack-path hypotheses, prioritize contextual risk, and produce actionable remediation guidance.

See the complete [project motive, problem statement, objectives, and research direction](docs/project-motive.md).

## Current status: 0.1.0 foundation

Implemented and tested:

- Python package and Typer/Rich CLI foundation
- Idempotent local workspace initialization
- SQLite persistence with PostgreSQL-compatible SQLAlchemy models
- Explicitly authorized project creation and audit events
- Validated domain, IP, CIDR, and HTTP(S) URL scope records
- Inclusion/exclusion evaluation and target-specific intrusive-test approval
- Configuration validation, rotating logs, and secret redaction
- Workspace and database diagnostics through `aegisx doctor`
- Canonical Pydantic finding/evidence contracts
- Unit, integration, and security tests

Not yet implemented: reconnaissance, network scanning, WAPT, API/LLM assessment, correlation, attack graphs, AI analysis, or reports. Commands for these capabilities are intentionally not exposed yet.

## Requirements

- Linux (Kali Linux, Ubuntu, or Debian)
- Python 3.11 or newer
- `venv` support (`python3-venv` on Debian-based systems)

Nmap, OWASP ZAP, NetworkX, HTTPX, and BeautifulSoup become runtime requirements in the phases that use them; Phase 1 does not install or claim those integrations.

## Development installation

```bash
cd /path/to/AEGISX
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Alternatively:

```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
source .venv/bin/activate
```

## Quick start

Running AEGISX without a command displays the logo and available commands:

```bash
aegisx
```

Initialize `.aegisx` under the current directory:

```bash
aegisx init
```

Create an authorized project. The confirmation flag must only be supplied after permission has actually been obtained:

```bash
aegisx project create "Authorized Lab" \
  --authorized-by "Lab Owner" \
  --authorization-reference "LAB-ROE-001" \
  --authorization-expires "2027-12-31T23:59:59+00:00" \
  --confirm-authorization \
  --actor "analyst@example.test"
```

Add targets and explicit exclusions:

```bash
aegisx scope add "192.0.2.0/24" \
  --project authorized-lab \
  --created-by "analyst@example.test"

aegisx scope add "192.0.2.25" \
  --project authorized-lab \
  --mode exclude \
  --created-by "analyst@example.test"

aegisx scope add "https://app.example.test/" \
  --project authorized-lab \
  --allow-intrusive \
  --intrusive-approval-reference "LAB-ROE-001-IT" \
  --created-by "analyst@example.test"
```

Inspect persisted state:

```bash
aegisx project list
aegisx scope show --project authorized-lab
aegisx scope show --project authorized-lab --output json
aegisx doctor
```

Use a workspace outside the current directory with either `--home` or `AEGISX_HOME`:

```bash
aegisx --home /secure/engagements/acme init
AEGISX_HOME=/secure/engagements/acme aegisx project list
```

## Test and quality commands

```bash
pytest
pytest --cov=aegisx --cov-report=term-missing
ruff check .
mypy aegisx
```

## Docker

```bash
docker build -t aegisx:0.1.0 .
docker run --rm -v "$PWD/.aegisx:/data" aegisx:0.1.0 init
docker run --rm -v "$PWD/.aegisx:/data" aegisx:0.1.0 project list
```

## Documentation

- [Project motive and long-term vision](docs/project-motive.md)
- [Phase 1 design and requirements mapping](docs/phase-1-foundation.md)
- [Security and authorization model](docs/security-model.md)
- [Security disclosure policy](SECURITY.md)
- [Contribution guide](CONTRIBUTING.md)

## Responsible use

AEGISX is for systems you own or have explicit authorization to assess. Project metadata does not grant legal permission; it records the authorization obtained outside the tool. Future engines must invoke the central scope authorization service before any target interaction.
