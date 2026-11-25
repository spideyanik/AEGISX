"""Foundation environment diagnostics."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import typer
from rich.table import Table
from sqlalchemy import text

from aegisx.commands.common import console, fail, get_runtime


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def run_doctor(context: typer.Context) -> None:
    """Validate the Python runtime, workspace, directories, and database connection."""
    checks = [
        Check(
            name="Python",
            passed=sys.version_info >= (3, 11),
            detail=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    ]
    try:
        runtime = get_runtime(context)
        checks.append(Check("Configuration", True, str(runtime.settings.config_path)))
        checks.append(
            Check(
                "Workspace writable",
                os.access(runtime.settings.home, os.W_OK),
                str(runtime.settings.home),
            )
        )
        with runtime.database.session() as session:
            session.execute(text("SELECT 1"))
        checks.append(Check("Database", True, "connection and transaction successful"))
        for directory_name in ("logs", "evidence", "exports"):
            directory = runtime.settings.home / directory_name
            checks.append(
                Check(
                    f"Directory: {directory_name}",
                    directory.is_dir() and os.access(directory, os.W_OK),
                    str(directory),
                )
            )
    except Exception as exc:
        fail(exc)

    table = Table(title="AEGISX Foundation Diagnostics")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in checks:
        table.add_row(
            check.name,
            "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]",
            check.detail,
        )
    console.print(table)
    if not all(check.passed for check in checks):
        raise typer.Exit(code=1)
