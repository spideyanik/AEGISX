"""Application logging with conservative secret redaction."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)([^\s,;]+)"),
    re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(https?://[^:/\s]+:)([^@/\s]+)(@)"),
)


def redact_text(value: str) -> str:
    """Redact common credential forms without mutating unrelated text."""
    redacted = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 3:
            redacted = pattern.sub(r"\1[REDACTED]\3", redacted)
        else:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


class SecretRedactionFilter(logging.Filter):
    """Redact secrets after log message interpolation."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        return True


def configure_logging(log_path: Path, level: str, *, redact_secrets: bool = True) -> None:
    """Configure a rotating file handler once per process."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aegisx")
    logger.setLevel(level.upper())
    logger.propagate = False

    expected_path = str(log_path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and handler.baseFilename == expected_path:
            return

    handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    log_path.chmod(0o640)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    if redact_secrets:
        handler.addFilter(SecretRedactionFilter())
    logger.addHandler(handler)
