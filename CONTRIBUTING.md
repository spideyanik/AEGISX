# Contributing to AEGISX

AEGISX is developed incrementally. Contributions must align with the active roadmap phase and must not expose a command before its implementation is functional and tested.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Required checks

```bash
pytest
ruff check .
mypy aegisx
```

## Engineering requirements

- Preserve backward-compatible behavior unless a documented migration is included.
- Use the canonical finding and evidence contracts.
- Enforce project scope before any target interaction.
- Validate every redirect destination before following it.
- Apply central rate and concurrency limits.
- Require separate approval for intrusive tests.
- Never pass AI-generated text directly to a shell.
- Avoid logging credentials or sensitive evidence.
- Include unit, integration, and security tests for changed behavior.
- Clearly distinguish observed facts, hypotheses, and validated attack paths.

## Pull requests

Describe the implemented behavior, safety implications, test evidence, and any pending work. Do not describe placeholders or experimental behavior as completed functionality.
