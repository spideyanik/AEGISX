"""Project and authorized scope management services."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aegisx.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from aegisx.core.scope import NormalizedTarget, ScopeMode, normalize_target, scope_contains
from aegisx.database.models import AuditLog, Project, Scope


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValidationError("Project name must contain at least one letter or number.")
    return slug[:128]


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ProjectService:
    """Perform validated project and scope operations in one transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_project(
        self,
        *,
        name: str,
        description: str,
        authorization_reference: str,
        authorized_by: str,
        authorization_expires_at: datetime | None,
        actor: str,
        authorization_confirmed: bool,
    ) -> Project:
        clean_name = name.strip()
        reference = authorization_reference.strip()
        authorizer = authorized_by.strip()
        if not authorization_confirmed:
            raise AuthorizationError(
                "Explicit authorization confirmation is required. Use --confirm-authorization only "
                "when you possess permission to assess the targets."
            )
        if not clean_name or len(clean_name) > 128:
            raise ValidationError("Project name must contain 1 to 128 characters.")
        if not reference or not authorizer:
            raise AuthorizationError(
                "An authorization reference and authorizing party are required."
            )
        expiry = _as_utc(authorization_expires_at) if authorization_expires_at else None
        if expiry is not None and expiry <= datetime.now(UTC):
            raise AuthorizationError("Project authorization expiry must be in the future.")

        project = Project(
            name=clean_name,
            slug=_slugify(clean_name),
            description=description.strip(),
            authorization_reference=reference,
            authorized_by=authorizer,
            authorization_expires_at=expiry,
        )
        self.session.add(project)
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise ConflictError(f"A project named '{clean_name}' already exists.") from exc
        self._audit(
            project_id=project.id,
            actor=actor,
            action="project.create",
            resource_type="project",
            resource_id=project.id,
            details={
                "name": project.name,
                "authorization_reference": project.authorization_reference,
                "authorized_by": project.authorized_by,
            },
        )
        return project

    def list_projects(self) -> list[Project]:
        return list(self.session.scalars(select(Project).order_by(Project.created_at.desc())))

    def get_project(self, identifier: str) -> Project:
        candidate = identifier.strip()
        project = self.session.scalar(
            select(Project).where(
                (Project.id == candidate)
                | (Project.name == candidate)
                | (Project.slug == candidate)
            )
        )
        if project is None:
            raise NotFoundError(f"Project '{identifier}' was not found.")
        return project

    def add_scope(
        self,
        *,
        project_identifier: str,
        value: str,
        target_type: str,
        mode: str,
        created_by: str,
        approved_for_intrusive: bool,
        intrusive_approval_reference: str | None,
        require_intrusive_approval: bool,
    ) -> Scope:
        project = self.get_project(project_identifier)
        self._require_active_authorization(project)
        try:
            scope_mode = ScopeMode(mode)
        except ValueError as exc:
            raise ValidationError("Scope mode must be 'include' or 'exclude'.") from exc
        normalized = normalize_target(value, target_type)
        approval_reference = (intrusive_approval_reference or "").strip() or None
        if approved_for_intrusive and require_intrusive_approval and not approval_reference:
            raise AuthorizationError(
                "Intrusive scope requires --intrusive-approval-reference."
            )
        if scope_mode is ScopeMode.EXCLUDE and approved_for_intrusive:
            raise ValidationError("Excluded scope cannot be approved for intrusive testing.")
        if not created_by.strip():
            raise ValidationError("The scope creator must be identified.")

        scope = Scope(
            project_id=project.id,
            target_type=normalized.target_type.value,
            value=value.strip(),
            normalized_value=normalized.value,
            mode=scope_mode.value,
            approved_for_intrusive=approved_for_intrusive,
            intrusive_approval_reference=approval_reference,
            created_by=created_by.strip(),
        )
        self.session.add(scope)
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise ConflictError(
                f"Scope '{normalized.value}' ({scope_mode.value}) already exists in this project."
            ) from exc
        self._audit(
            project_id=project.id,
            actor=created_by,
            action="scope.add",
            resource_type="scope",
            resource_id=scope.id,
            details={
                "target_type": scope.target_type,
                "normalized_value": scope.normalized_value,
                "mode": scope.mode,
                "approved_for_intrusive": scope.approved_for_intrusive,
            },
        )
        return scope

    def list_scopes(self, project_identifier: str) -> tuple[Project, list[Scope]]:
        project = self.get_project(project_identifier)
        scopes = list(
            self.session.scalars(
                select(Scope).where(Scope.project_id == project.id).order_by(Scope.created_at)
            )
        )
        return project, scopes

    def is_target_authorized(
        self, project_identifier: str, target: str, *, intrusive: bool = False
    ) -> bool:
        """Enforce inclusions, exclusions, expiry, and intrusive-test approval."""
        project, scopes = self.list_scopes(project_identifier)
        self._require_active_authorization(project)
        matches: list[Scope] = []
        for record in scopes:
            normalized_scope = NormalizedTarget(
                target_type=normalize_target(
                    record.normalized_value, record.target_type
                ).target_type,
                value=record.normalized_value,
            )
            if scope_contains(normalized_scope, target):
                if record.mode == ScopeMode.EXCLUDE.value:
                    return False
                matches.append(record)
        if not matches:
            return False
        return not intrusive or any(record.approved_for_intrusive for record in matches)

    @staticmethod
    def _require_active_authorization(project: Project) -> None:
        if project.status != "active":
            raise AuthorizationError(f"Project '{project.name}' is not active.")
        if project.authorization_expires_at is not None:
            expiry = _as_utc(project.authorization_expires_at)
            if expiry <= datetime.now(UTC):
                raise AuthorizationError(f"Authorization for project '{project.name}' has expired.")

    def _audit(
        self,
        *,
        project_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, object],
    ) -> None:
        self.session.add(
            AuditLog(
                project_id=project_id,
                actor=actor.strip() or "unknown",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                success=True,
            )
        )
