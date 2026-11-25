"""Authorized target scope commands."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from aegisx.commands.common import console, fail, get_runtime, print_json
from aegisx.core.exceptions import ValidationError
from aegisx.core.projects import ProjectService

app = typer.Typer(help="Add and inspect validated project scope.", no_args_is_help=True)


@app.command("add")
def add_scope(
    context: typer.Context,
    target: Annotated[str, typer.Argument(help="Domain, IP, CIDR, or HTTP(S) URL.")],
    project: Annotated[
        str, typer.Option("--project", "-p", help="Project ID, exact name, or slug.")
    ],
    target_type: Annotated[
        str,
        typer.Option(
            "--type", help="Target type: auto, domain, ip, cidr, or url."
        ),
    ] = "auto",
    mode: Annotated[
        str, typer.Option("--mode", help="Whether the target is included or excluded.")
    ] = "include",
    created_by: Annotated[
        str, typer.Option("--created-by", help="Operator recorded in the audit log.")
    ] = "local-operator",
    allow_intrusive: Annotated[
        bool,
        typer.Option(
            "--allow-intrusive", help="Mark this target as separately approved for intrusive tests."
        ),
    ] = False,
    intrusive_approval_reference: Annotated[
        str | None,
        typer.Option(
            "--intrusive-approval-reference",
            help="Ticket or rules-of-engagement reference for intrusive tests.",
        ),
    ] = None,
) -> None:
    """Validate and add an inclusion or exclusion to a project."""
    try:
        runtime = get_runtime(context)
        with runtime.database.session() as session:
            record = ProjectService(session).add_scope(
                project_identifier=project,
                value=target,
                target_type=target_type,
                mode=mode,
                created_by=created_by,
                approved_for_intrusive=allow_intrusive,
                intrusive_approval_reference=intrusive_approval_reference,
                require_intrusive_approval=runtime.settings.require_intrusive_approval,
            )
            record_id = record.id
            normalized = record.normalized_value
            kind = record.target_type
    except Exception as exc:
        fail(exc)
    console.print(
        f"[green]Added {kind} scope[/green] {normalized} [dim]({record_id})[/dim]"
    )


@app.command("show")
def show_scope(
    context: typer.Context,
    project: Annotated[
        str, typer.Option("--project", "-p", help="Project ID, exact name, or slug.")
    ],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: table or json.")
    ] = "table",
) -> None:
    """Show the normalized scope for one project."""
    try:
        runtime = get_runtime(context)
        with runtime.database.session() as session:
            selected_project, records = ProjectService(session).list_scopes(project)
            project_data = {"id": selected_project.id, "name": selected_project.name}
            rows = [
                {
                    "id": item.id,
                    "target_type": item.target_type,
                    "original_value": item.value,
                    "normalized_value": item.normalized_value,
                    "mode": item.mode,
                    "approved_for_intrusive": item.approved_for_intrusive,
                    "created_by": item.created_by,
                    "created_at": item.created_at,
                }
                for item in records
            ]
    except Exception as exc:
        fail(exc)

    if output == "json":
        print_json({"project": project_data, "scopes": rows})
        return
    if output != "table":
        fail(ValidationError("Output format must be 'table' or 'json'."))
    table = Table(title=f"Scope: {project_data['name']}")
    table.add_column("Mode")
    table.add_column("Type")
    table.add_column("Normalized target", style="cyan")
    table.add_column("Intrusive")
    table.add_column("Added by")
    for row in rows:
        table.add_row(
            str(row["mode"]),
            str(row["target_type"]),
            str(row["normalized_value"]),
            "yes" if row["approved_for_intrusive"] else "no",
            str(row["created_by"]),
        )
    console.print(table)
