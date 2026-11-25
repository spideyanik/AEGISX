"""Target normalization and scope-boundary matching."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit

from aegisx.core.exceptions import ValidationError

DOMAIN_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


class ScopeTargetType(StrEnum):
    DOMAIN = "domain"
    IP = "ip"
    CIDR = "cidr"
    URL = "url"


class ScopeMode(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


@dataclass(frozen=True)
class NormalizedTarget:
    target_type: ScopeTargetType
    value: str


def _normalize_domain(value: str, *, allow_wildcard: bool = True) -> str:
    domain = value.strip().rstrip(".").lower()
    wildcard = domain.startswith("*.")
    if wildcard:
        if not allow_wildcard:
            raise ValidationError("Wildcards are not valid in this target.")
        domain = domain[2:]
    if not domain or len(domain) > 253:
        raise ValidationError("Domain must contain between 1 and 253 characters.")
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValidationError(f"Invalid internationalized domain: {value}") from exc
    labels = ascii_domain.split(".")
    if len(labels) < 2 or any(not DOMAIN_LABEL.fullmatch(label) for label in labels):
        raise ValidationError(f"Invalid fully qualified domain: {value}")
    return f"*.{ascii_domain}" if wildcard else ascii_domain


def _normalize_ip(value: str) -> str:
    try:
        return ipaddress.ip_address(value.strip()).compressed
    except ValueError as exc:
        raise ValidationError(f"Invalid IP address: {value}") from exc


def _normalize_cidr(value: str) -> str:
    try:
        return ipaddress.ip_network(value.strip(), strict=True).compressed
    except ValueError as exc:
        raise ValidationError(
            f"Invalid CIDR network: {value}. Use the network address, not a host address."
        ) from exc


def _normalize_url(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as exc:
        raise ValidationError(f"Invalid URL: {value}") from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValidationError("URL scope supports only http and https schemes.")
    if not parsed.hostname:
        raise ValidationError("URL scope requires a hostname.")
    if parsed.username or parsed.password:
        raise ValidationError("Credentials must not be embedded in scope URLs.")
    if parsed.query or parsed.fragment:
        raise ValidationError("Scope URLs must not include query strings or fragments.")

    hostname: str
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        hostname = f"[{ip.compressed}]" if ip.version == 6 else ip.compressed
    except ValueError:
        hostname = _normalize_domain(parsed.hostname, allow_wildcard=False)

    scheme = parsed.scheme.lower()
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"
    path = parsed.path or "/"
    normalized_path = "/" + "/".join(segment for segment in path.split("/") if segment)
    if path.endswith("/") and normalized_path != "/":
        normalized_path += "/"
    return urlunsplit((scheme, netloc, normalized_path, "", ""))


def detect_target_type(value: str) -> ScopeTargetType:
    """Detect a supported target type without broadening malformed values."""
    candidate = value.strip()
    if candidate.lower().startswith(("http://", "https://")):
        return ScopeTargetType.URL
    if "/" in candidate:
        return ScopeTargetType.CIDR
    try:
        ipaddress.ip_address(candidate)
        return ScopeTargetType.IP
    except ValueError:
        return ScopeTargetType.DOMAIN


def normalize_target(value: str, target_type: ScopeTargetType | str = "auto") -> NormalizedTarget:
    """Validate and canonicalize an IP, CIDR, domain, or HTTP(S) URL."""
    try:
        resolved_type = (
            detect_target_type(value) if target_type == "auto" else ScopeTargetType(target_type)
        )
    except ValueError as exc:
        supported = ", ".join(item.value for item in ScopeTargetType)
        raise ValidationError(f"Unsupported target type. Choose auto, {supported}.") from exc

    normalizers = {
        ScopeTargetType.DOMAIN: _normalize_domain,
        ScopeTargetType.IP: _normalize_ip,
        ScopeTargetType.CIDR: _normalize_cidr,
        ScopeTargetType.URL: _normalize_url,
    }
    return NormalizedTarget(resolved_type, normalizers[resolved_type](value))


def scope_contains(scope: NormalizedTarget, candidate_value: str) -> bool:
    """Return whether a normalized scope contains a candidate target."""
    try:
        candidate = normalize_target(candidate_value)
    except ValidationError:
        return False

    if scope.target_type is ScopeTargetType.IP:
        if candidate.target_type is ScopeTargetType.IP:
            return scope.value == candidate.value
        if candidate.target_type is ScopeTargetType.URL:
            return _url_hostname(candidate.value) == scope.value
        return False

    if scope.target_type is ScopeTargetType.CIDR:
        network = ipaddress.ip_network(scope.value)
        candidate_host = (
            candidate.value
            if candidate.target_type is ScopeTargetType.IP
            else _url_hostname(candidate.value)
            if candidate.target_type is ScopeTargetType.URL
            else None
        )
        if candidate_host is None:
            return False
        try:
            return ipaddress.ip_address(candidate_host) in network
        except ValueError:
            return False

    if scope.target_type is ScopeTargetType.DOMAIN:
        candidate_host = (
            candidate.value
            if candidate.target_type is ScopeTargetType.DOMAIN
            else _url_hostname(candidate.value)
            if candidate.target_type is ScopeTargetType.URL
            else ""
        )
        if scope.value.startswith("*."):
            suffix = scope.value[1:]
            return candidate_host.endswith(suffix) and candidate_host != scope.value[2:]
        return candidate_host == scope.value

    if scope.target_type is ScopeTargetType.URL and candidate.target_type is ScopeTargetType.URL:
        allowed = urlsplit(scope.value)
        tested = urlsplit(candidate.value)
        allowed_path = allowed.path.rstrip("/") or "/"
        tested_path = tested.path.rstrip("/") or "/"
        path_matches = (
            allowed_path == "/"
            or tested_path == allowed_path
            or tested_path.startswith(f"{allowed_path}/")
        )
        return (
            allowed.scheme == tested.scheme
            and allowed.netloc == tested.netloc
            and path_matches
        )
    return False


def _url_hostname(value: str) -> str:
    return urlsplit(value).hostname or ""
