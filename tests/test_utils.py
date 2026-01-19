"""Tests for utility modules."""

from unittest.mock import patch

from dotfiles_maintainer.utils.secrets import redact_secrets


def test_redact_secrets_basic():
    text = "My api_key: '123456789012345678901'"
    expected = "My api_key: [REDACTED]"
    assert redact_secrets(text) == expected


def test_redact_secrets_openai():
    text = "Key: sk-123456789012345678901234567890123456789012345678"
    expected = "Key: [OPENAI_API_KEY_REDACTED]"
    assert redact_secrets(text) == expected


def test_redact_secrets_google():
    text = "Key: AIzaSyA-BC12345678901234567890123456789"
    expected = "Key: [GOOGLE_API_KEY_REDACTED]"
    assert redact_secrets(text) == expected


def test_redact_secrets_password():
    text = "password = 'supersecretpassword'"
    expected = "password: [REDACTED]"
    assert redact_secrets(text) == expected


def test_redact_secrets_no_secrets():
    text = "This is a safe string."
    assert redact_secrets(text) == text


def test_redact_secrets_empty():
    assert redact_secrets("") == ""
    assert redact_secrets(None) is None  # type: ignore


def test_redact_secrets_failure():
    """Test redaction failure path."""
    with patch("re.sub", side_effect=Exception("regex error")):
        # Should return original text on failure
        assert redact_secrets("my secret") == "my secret"
