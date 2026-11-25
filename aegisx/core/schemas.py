"""Stable finding and evidence contracts for all future assessment engines."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    OBSERVED = "observed"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    REMEDIATED = "remediated"


class EvidenceRecord(BaseModel):
    """Evidence metadata; large or sensitive content remains in protected storage."""

    model_config = ConfigDict(extra="forbid")

    evidence_type: str = Field(min_length=1, max_length=64)
    summary: str = Field(min_length=1, max_length=2000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_path: str | None = None
    collected_at: datetime


class FindingRecord(BaseModel):
    """Canonical finding produced by every assessment engine."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=128)
    affected_asset_id: UUID
    severity: Severity
    confidence: Confidence
    verification_status: VerificationStatus
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    remediation: str = Field(min_length=1)
    timestamp: datetime
    assessment_source: str = Field(min_length=1, max_length=128)
