from pathlib import Path

import pytest
from typer.testing import CliRunner

from aegisx.cli import app

runner = CliRunner()


@pytest.mark.integration
def test_initialize_create_project_and_add_scope(tmp_path: Path) -> None:
    home = tmp_path / "workspace"

    initialized = runner.invoke(app, ["--home", str(home), "init"])
    assert initialized.exit_code == 0, initialized.output
    assert (home / "config.toml").is_file()
    assert (home / "aegisx.db").is_file()

    diagnostics = runner.invoke(app, ["--home", str(home), "doctor"])
    assert diagnostics.exit_code == 0, diagnostics.output
    assert "Database" in diagnostics.output
    assert "PASS" in diagnostics.output

    created = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "project",
            "create",
            "Authorized Lab",
            "--authorized-by",
            "Lab Owner",
            "--authorization-reference",
            "LAB-ROE-001",
            "--confirm-authorization",
            "--actor",
            "tester",
        ],
    )
    assert created.exit_code == 0, created.output
    assert "Created project" in created.output

    added = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "scope",
            "add",
            "EXAMPLE.com.",
            "--project",
            "authorized-lab",
            "--created-by",
            "tester",
        ],
    )
    assert added.exit_code == 0, added.output
    assert "example.com" in added.output

    shown = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "scope",
            "show",
            "--project",
            "authorized-lab",
            "--output",
            "json",
        ],
    )
    assert shown.exit_code == 0, shown.output
    assert '"normalized_value": "example.com"' in shown.output


@pytest.mark.integration
def test_project_creation_requires_authorization_confirmation(tmp_path: Path) -> None:
    home = tmp_path / "workspace"
    assert runner.invoke(app, ["--home", str(home), "init"]).exit_code == 0

    result = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "project",
            "create",
            "Unconfirmed",
            "--authorized-by",
            "Owner",
            "--authorization-reference",
            "ROE-002",
        ],
    )
    assert result.exit_code == 1
    assert "Explicit authorization confirmation is required" in result.output
