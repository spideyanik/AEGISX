from aegisx.core.logging import redact_text


def test_redacts_common_secret_forms() -> None:
    message = "Authorization: Bearer abc123 password=hunter2 api_key=key-value"
    redacted = redact_text(message)
    assert "abc123" not in redacted
    assert "hunter2" not in redacted
    assert "key-value" not in redacted
    assert redacted.count("[REDACTED]") == 3


def test_redacts_url_password() -> None:
    redacted = redact_text("requesting https://operator:secret@example.com/api")
    assert redacted == "requesting https://operator:[REDACTED]@example.com/api"
