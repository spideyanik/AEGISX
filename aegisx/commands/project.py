"""Database-backed project management commands."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import typer
from rich.table import Table

from aegisx.commands.common import console, fail, get_runtime, print_json
from aegisx.core.exceptions import ValidationError
from aegisx.core.projects import ProjectService

app = typer.Typer(help="Create and inspect authorized assessment projects.", no_args_is_help=True)


def _parse_expiry(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise typer.BadParameter(
            "Use ISO 8601, for example 2027-12-31T23:59:59+00:00."
        ) from exc


@app.command("create")
def create_project(
    context: typer.Context,
    name: Annotated[str, typer.Argument(help="Unique project name.")],
    authorized_by: Annotated[
        str, typer.Option("--authorized-by", help="Person or organization granting permission.")
    ],
    authorization_reference: Annotated[
        str,
        typer.Option(
            "--authorization-reference",
            help="Contract, ticket, rules-of-engagement, or lab authorization reference.",
        ),
    ],
    confirm_authorization: Annotated[
        bool,
        typer.Option(
            "--confirm-authorization",
            help="Confirm that explicit authorization has been obtained.",
        ),
    ] = False,
    description: Annotated[
        str, typer.Option("--description", "-d", help="Project description.")
    ] = "",
    authorization_expires: Annotated[
        str | None,
        typer.Option("--authorization-expires", help="Optional ISO 8601 authorization expiry."),
    ] = None,
    actor: Annotated[
        str, typer.Option("--actor", help="Operator recorded in the audit log.")
    ] = "local-operator",
) -> None:
    """Create a project only after explicit authorization is recorded."""
    try:
        runtime = get_runtime(context)
        expiry = _parse_expiry(authorization_expires)
        with runtime.database.session() as session:
            project = ProjectService(session).create_project(
                name=name,
                description=description,
                authorization_reference=authorization_reference,
                authorized_by=authorized_by,
                authorization_expires_at=expiry,
                actor=actor,
                authorization_confirmed=confirm_authorization,
            )
            project_id = project.id
            project_name = project.name
    except typer.BadParameter:
        raise
    except Exception as exc:
        fail(exc)
    console.print(f"[green]Created project[/green] {project_name} [dim]({project_id})[/dim]")


@app.command("list")
def list_projects(
    context: typer.Context,
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: table or json.")
    ] = "table",
) -> None:
    """List all projects in the active workspace."""
    try:
        runtime = get_runtime(context)
        with runtime.database.session() as session:
            projects = ProjectService(session).list_projects()
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "status": item.status,
                    "authorized_by": item.authorized_by,
                    "authorization_reference": item.authorization_reference,
                    "authorization_expires_at": item.authorization_expires_at,
                    "created_at": item.created_at,
                }
                for item in projects
            ]
    except Exception as exc:
        fail(exc)

    if output == "json":
        print_json(rows)
        return
    if output != "table":
        fail(ValidationError("Output format must be 'table' or 'json'."))
    table = Table(title="AEGISX Projects")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Authorized by")
    table.add_column("Expires")
    for row in rows:
        table.add_row(
            str(row["id"]),
            str(row["name"]),
            str(row["status"]),
            str(row["authorized_by"]),
            str(row["authorization_expires_at"] or "not set"),
        )
    console.print(table)
