"""Tests for persona prompts."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from dotfiles_maintainer.prompts.persona import (
    dotmate_persona,
    pre_change,
    register_persona_prompts,
    session_start,
)
from mcp.types import TextContent


def test_dotmate_persona():
    """Test loading persona from file."""
    mock_content = "Mock Persona Content"
    with patch(
        "builtins.open",
        MagicMock(
            return_value=MagicMock(
                __enter__=MagicMock(
                    return_value=MagicMock(read=MagicMock(return_value=mock_content))
                )
            )
        ),
    ):
        messages = dotmate_persona()
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        content = messages[0].content
        assert isinstance(content, TextContent)
        assert content.text == mock_content


def test_session_start():
    """Test session start prompt."""
    messages = session_start()
    assert len(messages) == 1
    assert messages[0].role == "user"
    content = messages[0].content
    assert isinstance(content, TextContent)
    assert "Session Start Workflow" in content.text


def test_pre_change():
    """Test pre-change prompt."""
    messages = pre_change()
    assert len(messages) == 1
    assert messages[0].role == "user"
    content = messages[0].content
    assert isinstance(content, TextContent)
    assert "Pre-Change Safety Checklist" in content.text


def test_register_persona_prompts():
    """Test prompt registration."""
    mock_mcp = MagicMock()
    register_persona_prompts(mock_mcp)
    # Check if mcp.prompt was called for each prompt
    assert mock_mcp.prompt.call_count == 3
