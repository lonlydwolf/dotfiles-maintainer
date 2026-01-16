"""Secrets security utils."""

import logging
import re

logger = logging.getLogger(__name__)


def redact_secrets(text: str | None) -> str | None:
    """Automatically redact sensitive data before storing in memory."""
    if not text:
        return text

    patterns = [
        # Generic patterns
        (r"(?i)api_key\s*[:=]\s*[^\s]+", "api_key: [REDACTED]"),
        (r"(?i)token\s*[:=]\s*[^\s]+", "token: [REDACTED]"),
        (r"(?i)password\s*[:=]\s*[^\s]+", "password: [REDACTED]"),
        # Provider specific
        (r"AIzaSy[a-zA-Z0-9_\-]{33}", "[GOOGLE_API_KEY_REDACTED]"),
        (r"sk-[a-zA-Z0-9]{48}", "[OPENAI_API_KEY_REDACTED]"),
        (r"sk-proj-[a-zA-Z0-9_\-]{20,}", "[OPENAI_PROJECT_KEY_REDACTED]"),
        (r"sk-ant-[a-zA-Z0-9_\-]{20,}", "[ANTHROPIC_API_KEY_REDACTED]"),
        (r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN_REDACTED]"),
        (r"(AKIA|ASIA)[0-9A-Z]{16}", "[AWS_ACCESS_KEY_REDACTED]"),
        (r"xox[baprs]-[a-zA-Z0-9]{10,48}", "[SLACK_TOKEN_REDACTED]"),
        (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "[PRIVATE_KEY_BLOCK_REDACTED]"),
    ]

    redacted = text
    for pattern, replacement in patterns:
        try:
            redacted = re.sub(pattern, replacement, redacted)
        except Exception as e:
            logger.debug(f"Redaction failed: {e}")

    return redacted
