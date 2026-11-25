from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aegisx.core.schemas import (
    Confidence,
    EvidenceRecord,
    FindingRecord,
    Severity,
    VerificationStatus,
)


def test_standardized_finding_contract() -> None:
    finding = FindingRecord(
        id=uuid4(),
        title="Missing security header",
        description="The response did not include a Content-Security-Policy header.",
        category="security_headers",
        affected_asset_id=uuid4(),
        severity=Severity.LOW,
        confidence=Confidence.HIGH,
        verification_status=VerificationStatus.OBSERVED,
        evidence=[
            EvidenceRecord(
                evidence_type="http_response",
                summary="Header absent from response.",
                sha256="a" * 64,
                collected_at=datetime.now(UTC),
            )
        ],
        remediation="Define and test a restrictive Content-Security-Policy.",
        timestamp=datetime.now(UTC),
        assessment_source="test-engine",
    )
    assert finding.evidence[0].sha256 == "a" * 64


def test_evidence_requires_sha256_digest() -> None:
    with pytest.raises(ValidationError):
        EvidenceRecord(
            evidence_type="response",
            summary="Invalid digest test.",
            sha256="not-a-digest",
            collected_at=datetime.now(UTC),
        )
