"""Safe, idempotent workspace initialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aegisx.core.config import CONFIG_FILENAME, Settings, load_settings
from aegisx.database.session import Database

DEFAULT_CONFIG = """# AEGISX workspace configuration
[aegisx]
# Empty uses <workspace>/aegisx.db. PostgreSQL URLs are also supported.
database_url = ""
log_level = "INFO"

[safety]
max_concurrency = 4
requests_per_second = 2.0
redact_secrets = true
require_intrusive_approval = true
"""


@dataclass(frozen=True)
class InitializationResult:
    """Result of initializing a workspace."""

    home: Path
    created_config: bool


def initialize_workspace(home: Path) -> InitializationResult:
    """Create workspace directories, configuration, and database schema."""
    resolved_home = home.expanduser().resolve()
    resolved_home.mkdir(mode=0o750, parents=True, exist_ok=True)
    for directory in ("logs", "evidence", "exports"):
        (resolved_home / directory).mkdir(mode=0o750, exist_ok=True)

    config_path = resolved_home / CONFIG_FILENAME
    created_config = False
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
        config_path.chmod(0o640)
        created_config = True

    settings: Settings = load_settings(explicit_home=resolved_home)
    Database(settings.database_url).initialize_schema()
    local_database = resolved_home / "aegisx.db"
    if local_database.is_file():
        local_database.chmod(0o640)
    return InitializationResult(home=resolved_home, created_config=created_config)
