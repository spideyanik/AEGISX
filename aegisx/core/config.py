"""Workspace discovery and validated application configuration."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError

from aegisx.core.exceptions import ConfigurationError, WorkspaceNotInitializedError

CONFIG_FILENAME = "config.toml"
WORKSPACE_DIRECTORY = ".aegisx"


class Settings(BaseModel):
    """Runtime configuration loaded from a workspace and environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    home: Path
    database_url: str
    log_level: str = "INFO"
    max_concurrency: int = Field(default=4, ge=1, le=32)
    requests_per_second: float = Field(default=2.0, gt=0, le=100)
    redact_secrets: bool = True
    require_intrusive_approval: bool = True

    @property
    def config_path(self) -> Path:
        return self.home / CONFIG_FILENAME

    @property
    def log_path(self) -> Path:
        return self.home / "logs" / "aegisx.log"


def discover_home(start: Path | None = None, explicit_home: Path | None = None) -> Path:
    """Find a workspace by explicit path, environment, or parent traversal."""
    if explicit_home is not None:
        return explicit_home.expanduser().resolve()

    environment_home = os.getenv("AEGISX_HOME")
    if environment_home:
        return Path(environment_home).expanduser().resolve()

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        workspace = candidate / WORKSPACE_DIRECTORY
        if (workspace / CONFIG_FILENAME).is_file():
            return workspace
    return current / WORKSPACE_DIRECTORY


def load_settings(
    *, start: Path | None = None, explicit_home: Path | None = None
) -> Settings:
    """Load validated settings, with AEGISX_* environment overrides."""
    home = discover_home(start=start, explicit_home=explicit_home)
    config_path = home / CONFIG_FILENAME
    if not config_path.is_file():
        raise WorkspaceNotInitializedError(
            f"No AEGISX workspace found at {home}. Run 'aegisx init' first."
        )

    try:
        with config_path.open("rb") as config_file:
            raw = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(f"Unable to read {config_path}: {exc}") from exc

    app_values = raw.get("aegisx", {})
    safety_values = raw.get("safety", {})
    if not isinstance(app_values, dict) or not isinstance(safety_values, dict):
        raise ConfigurationError("Configuration sections [aegisx] and [safety] must be tables.")

    database_url = str(app_values.get("database_url", "")).strip()
    if not database_url:
        database_url = f"sqlite:///{(home / 'aegisx.db').as_posix()}"
    elif database_url.startswith("sqlite:///./"):
        relative_path = database_url.removeprefix("sqlite:///./")
        database_url = f"sqlite:///{(home / relative_path).as_posix()}"

    values: dict[str, Any] = {
        "home": home,
        "database_url": database_url,
        "log_level": app_values.get("log_level", "INFO"),
        "max_concurrency": safety_values.get("max_concurrency", 4),
        "requests_per_second": safety_values.get("requests_per_second", 2.0),
        "redact_secrets": safety_values.get("redact_secrets", True),
        "require_intrusive_approval": safety_values.get("require_intrusive_approval", True),
    }

    environment_overrides = {
        "database_url": "AEGISX_DATABASE_URL",
        "log_level": "AEGISX_LOG_LEVEL",
        "max_concurrency": "AEGISX_MAX_CONCURRENCY",
        "requests_per_second": "AEGISX_REQUESTS_PER_SECOND",
        "redact_secrets": "AEGISX_REDACT_SECRETS",
        "require_intrusive_approval": "AEGISX_REQUIRE_INTRUSIVE_APPROVAL",
    }
    for field, variable in environment_overrides.items():
        if variable in os.environ:
            values[field] = os.environ[variable]

    try:
        settings = Settings.model_validate(values)
    except PydanticValidationError as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc

    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if settings.log_level.upper() not in valid_levels:
        raise ConfigurationError(f"log_level must be one of: {', '.join(sorted(valid_levels))}")
    return settings
