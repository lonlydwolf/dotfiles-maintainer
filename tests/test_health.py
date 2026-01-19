"""Tests for the health check tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.config import ServerConfig
from dotfiles_maintainer.core.memory import MemoryManager
from dotfiles_maintainer.tools.health import health_check


@pytest.fixture
def mock_config():
    config = MagicMock(spec=ServerConfig)
    config.llm_key = "test-key"
    config.llm_provider = "google"
    return config


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock(spec=MemoryManager)
    manager.search = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_health_check_healthy(mock_config, mock_memory_manager):
    """Test health check when all components are healthy."""
    mock_memory_manager.search.return_value = {"results": []}

    with patch("dotfiles_maintainer.tools.health.detect_vcs_type", return_value="git"):
        status = await health_check(mock_config, mock_memory_manager)

        assert status["status"] == "healthy"
        assert status["components"]["memory"] == "connected"
        assert status["components"]["vcs"] == "active (git)"
        assert status["components"]["llm_provider"] == "configured (google)"


@pytest.mark.asyncio
async def test_health_check_memory_error(mock_config, mock_memory_manager):
    """Test health check when memory search fails."""
    mock_memory_manager.search.side_effect = Exception("Connection refused")

    with patch("dotfiles_maintainer.tools.health.detect_vcs_type", return_value="git"):
        status = await health_check(mock_config, mock_memory_manager)

        assert status["status"] == "unhealthy"
        assert "error" in status["components"]["memory"]
        assert status["components"]["memory"] == "error: Connection refused"


@pytest.mark.asyncio
async def test_health_check_vcs_error(mock_config, mock_memory_manager):
    """Test health check when VCS detection fails."""
    mock_memory_manager.search.return_value = {"results": []}

    with patch(
        "dotfiles_maintainer.tools.health.detect_vcs_type",
        side_effect=Exception("No VCS found"),
    ):
        status = await health_check(mock_config, mock_memory_manager)

        assert status["status"] == "unhealthy"
        assert "error" in status["components"]["vcs"]


@pytest.mark.asyncio
async def test_health_check_llm_missing_key(mock_config, mock_memory_manager):
    """Test health check when LLM key is missing."""
    mock_config.llm_key = None
    mock_memory_manager.search.return_value = {"results": []}

    with patch("dotfiles_maintainer.tools.health.detect_vcs_type", return_value="jj"):
        status = await health_check(mock_config, mock_memory_manager)

        assert status["status"] == "unhealthy"
        assert status["components"]["llm_provider"] == "missing_key"
