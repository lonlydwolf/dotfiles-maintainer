"""Tests for server configuration."""

import os
from unittest.mock import patch

from dotfiles_maintainer.config import ServerConfig


def test_server_config_ollama():
    """Test LLM config for ollama provider."""
    with patch.dict(
        os.environ,
        {"DOTMATE_LLM_PROVIDER": "ollama", "DOTMATE_LLM_KEY": "http://localhost:11434"},
    ):
        # Ensure we don't use cached settings if any
        config = ServerConfig()
        # Manually set because pydantic-settings might have already loaded defaults
        config.llm_provider = "ollama"
        config.llm_key = "http://localhost:11434"

        llm_cfg = config.llm_config
        assert llm_cfg.provider == "ollama"
        assert llm_cfg.config is not None
        assert llm_cfg.config["base_url"] == "http://localhost:11434"
