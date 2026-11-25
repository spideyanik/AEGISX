from pathlib import Path

import pytest

from aegisx.core.projects import ProjectService
from aegisx.database.session import Database


@pytest.mark.security
def test_exclusion_overrides_inclusion_and_intrusive_requires_approval(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    database.initialize_schema()

    with database.session() as session:
        service = ProjectService(session)
        service.create_project(
            name="Network Lab",
            description="Isolated test network",
            authorization_reference="LAB-001",
            authorized_by="Lab Owner",
            authorization_expires_at=None,
            actor="tester",
            authorization_confirmed=True,
        )
        service.add_scope(
            project_identifier="network-lab",
            value="10.10.0.0/16",
            target_type="auto",
            mode="include",
            created_by="tester",
            approved_for_intrusive=False,
            intrusive_approval_reference=None,
            require_intrusive_approval=True,
        )
        service.add_scope(
            project_identifier="network-lab",
            value="10.10.20.15",
            target_type="auto",
            mode="exclude",
            created_by="tester",
            approved_for_intrusive=False,
            intrusive_approval_reference=None,
            require_intrusive_approval=True,
        )

        assert service.is_target_authorized("network-lab", "10.10.30.8")
        assert not service.is_target_authorized("network-lab", "10.10.20.15")
        assert not service.is_target_authorized("network-lab", "10.11.1.1")
        assert not service.is_target_authorized("network-lab", "10.10.30.8", intrusive=True)


@pytest.mark.security
def test_intrusive_approval_is_target_specific(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    database.initialize_schema()

    with database.session() as session:
        service = ProjectService(session)
        service.create_project(
            name="Web Lab",
            description="Authorized application",
            authorization_reference="ROE-10",
            authorized_by="Application Owner",
            authorization_expires_at=None,
            actor="tester",
            authorization_confirmed=True,
        )
        service.add_scope(
            project_identifier="web-lab",
            value="https://app.example.test/",
            target_type="url",
            mode="include",
            created_by="tester",
            approved_for_intrusive=True,
            intrusive_approval_reference="ROE-10-INTRUSIVE",
            require_intrusive_approval=True,
        )
        assert service.is_target_authorized(
            "web-lab", "https://app.example.test/api", intrusive=True
        )
        assert not service.is_target_authorized(
            "web-lab", "https://other.example.test/api", intrusive=True
        )
