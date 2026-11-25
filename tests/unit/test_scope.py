import pytest

from aegisx.core.exceptions import ValidationError
from aegisx.core.scope import ScopeTargetType, normalize_target, scope_contains


@pytest.mark.parametrize(
    ("value", "expected_type", "expected_value"),
    [
        ("Example.COM.", ScopeTargetType.DOMAIN, "example.com"),
        ("192.0.2.10", ScopeTargetType.IP, "192.0.2.10"),
        ("2001:0db8::1", ScopeTargetType.IP, "2001:db8::1"),
        ("192.0.2.0/24", ScopeTargetType.CIDR, "192.0.2.0/24"),
        ("HTTPS://Example.COM:443/api/", ScopeTargetType.URL, "https://example.com/api/"),
    ],
)
def test_normalize_target(value: str, expected_type: ScopeTargetType, expected_value: str) -> None:
    result = normalize_target(value)
    assert result.target_type is expected_type
    assert result.value == expected_value


@pytest.mark.parametrize(
    "value",
    [
        "not a domain",
        "192.0.2.9/24",
        "ftp://example.com/files",
        "https://user:secret@example.com/",
        "https://example.com/?token=secret",
    ],
)
def test_rejects_unsafe_or_invalid_targets(value: str) -> None:
    with pytest.raises(ValidationError):
        normalize_target(value)


def test_scope_contains_cidr_member() -> None:
    scope = normalize_target("10.20.0.0/16")
    assert scope_contains(scope, "10.20.4.7")
    assert scope_contains(scope, "https://10.20.4.7/status")
    assert not scope_contains(scope, "10.21.4.7")


def test_domain_scope_does_not_implicitly_include_subdomains() -> None:
    assert not scope_contains(normalize_target("example.com"), "api.example.com")
    assert scope_contains(normalize_target("*.example.com"), "api.example.com")
    assert not scope_contains(normalize_target("*.example.com"), "example.com")


def test_url_scope_enforces_scheme_host_port_and_path_boundary() -> None:
    scope = normalize_target("https://example.com/api")
    assert scope_contains(scope, "https://example.com/api/v1")
    assert not scope_contains(scope, "https://example.com/api-v2")
    assert not scope_contains(scope, "http://example.com/api/v1")
    assert not scope_contains(scope, "https://other.example/api/v1")
