"""Shared command runtime and output helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console

from aegisx.core.config import Settings, load_settings
from aegisx.core.exceptions import AegisXError
from aegisx.core.logging import configure_logging
from aegisx.database.session import Database

console = Console()
error_console = Console(stderr=True)


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    database: Database


def explicit_home(context: typer.Context) -> Path | None:
    """Read the root-level workspace override inherited by subcommands."""
    root = context.find_root()
    if isinstance(root.obj, dict):
        value = root.obj.get("home")
        return Path(value) if value is not None else None
    return None


def get_runtime(context: typer.Context) -> Runtime:
    """Build the validated command runtime for an initialized workspace."""
    settings = load_settings(explicit_home=explicit_home(context))
    configure_logging(
        settings.log_path, settings.log_level, redact_secrets=settings.redact_secrets
    )
    database = Database(settings.database_url)
    database.initialize_schema()
    return Runtime(settings=settings, database=database)


def fail(error: Exception) -> NoReturn:
    """Present expected errors without a traceback or sensitive context."""
    if isinstance(error, AegisXError):
        message = str(error)
    else:
        logging.getLogger("aegisx").exception("Unexpected command failure")
        message = "Unexpected internal error. Review the workspace log for details."
    error_console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code=1)


def print_json(payload: object) -> None:
    console.print_json(json.dumps(payload, default=str))
