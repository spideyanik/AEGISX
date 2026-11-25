# Security and Authorization Model

## Authorization gate

A project cannot be created unless the operator records:

- The authorizing party.
- A contract, ticket, rules-of-engagement, or lab reference.
- An explicit `--confirm-authorization` assertion.
- An optional expiration timestamp.

This record is evidence of an operator assertion, not a substitute for legal authorization.

Future assessment engines must call `ProjectService.is_target_authorized()` immediately before network interaction. The method denies a target when:

- The project is inactive.
- Project authorization has expired.
- No inclusion contains the target.
- An exclusion contains the target.
- An intrusive operation is requested without target-specific intrusive approval.

## Scope semantics

- A plain domain includes only that exact domain.
- `*.example.com` includes subdomains but not the apex domain.
- A CIDR must use its network address; host bits are not silently discarded.
- A URL enforces scheme, authority, port, and path boundary.
- URL credentials, query strings, and fragments are rejected from scope records.
- Exclusions override inclusions.

Redirect-following code in later phases must validate every redirect destination through the same authorization gate before sending the next request.

## Intrusive assessments

Intrusive capability is denied by default. `--allow-intrusive` requires a separate approval reference when `require_intrusive_approval` is enabled. Future engines must classify their operations and request the intrusive authorization path where applicable.

## Rate and concurrency controls

Phase 1 validates `max_concurrency` and `requests_per_second` settings. No network engine exists yet, so there is nothing to throttle in this milestone. Future orchestrators must consume these central limits rather than defining unbounded engine-local defaults.

## Secrets and evidence

Common bearer tokens, passwords, API keys, and URL passwords are redacted from application log messages. Sensitive evidence must be stored beneath the workspace evidence directory rather than embedded in audit details. The canonical evidence contract requires a SHA-256 digest.

The current redaction filter is defense in depth, not permission to log credentials. Engine authors must avoid passing secrets to logs in the first place.

## AI execution boundary

The `aegisx.ai` namespace contains no execution capability in Phase 1. Later AI analysis must produce validated, structured plans consumed by a controlled assessment service. It must never pass model-generated text directly to a shell.
