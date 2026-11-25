from pathlib import Path

import pytest
from sqlalchemy import inspect

from aegisx.database.session import Database


@pytest.mark.integration
def test_initial_schema_contains_required_entities(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'schema.db'}")
    database.initialize_schema()

    assert set(inspect(database.engine).get_table_names()) == {
        "assets",
        "attack_paths",
        "audit_logs",
        "evidence",
        "findings",
        "projects",
        "relationships",
        "remediations",
        "scans",
        "scopes",
        "users",
    }
