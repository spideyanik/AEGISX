"""Top-level AEGISX command-line application."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aegisx import __version__
from aegisx.commands import doctor, project, scope
from aegisx.commands.common import console, explicit_home, fail
from aegisx.core.branding import show_logo
from aegisx.core.config import WORKSPACE_DIRECTORY
from aegisx.core.workspace import initialize_workspace

app = typer.Typer(
    name="aegisx",
    help="Evidence-driven, authorized cybersecurity assessment framework.",
    no_args_is_help=False,
    invoke_without_command=True,
    pretty_exceptions_enable=False,
)
app.add_typer(project.app, name="project")
app.add_typer(scope.app, name="scope")
app.command("doctor")(doctor.run_doctor)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"AEGISX {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    context: typer.Context,
    home: Annotated[
        Path | None,
        typer.Option(
            "--home",
            envvar="AEGISX_HOME",
            help="Workspace path. Defaults to a discovered .aegisx directory.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = None,
) -> None:
    """Configure global CLI options."""
    context.obj = {"home": home}
    if context.invoked_subcommand is None:
        show_logo(console)
        console.print(context.get_help())


@app.command("init")
def initialize(
    context: typer.Context,
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            help="Workspace directory. Defaults to <current directory>/.aegisx.",
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
) -> None:
    """Initialize configuration, protected directories, and the database schema."""
    target = path or explicit_home(context) or (Path.cwd() / WORKSPACE_DIRECTORY)
    show_logo(console)
    try:
        result = initialize_workspace(target)
    except Exception as exc:
        fail(exc)
    state = "Initialized" if result.created_config else "Verified existing"
    console.print(f"[green]{state} AEGISX workspace[/green] at {result.home}")
    console.print(f"Configuration: {result.home / 'config.toml'}")
