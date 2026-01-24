"""Tests to boost coverage for missing branches."""

import os
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError
from dotfiles_maintainer.config import ServerConfig
from dotfiles_maintainer.core.memory import MemoryManager, MemorySearchError
from dotfiles_maintainer.core.types import (
    Mem0AddResponse,
    Mem0GetAllResponse,
    Mem0DeleteResponse,
    SearchResult,
    AppConfig,
    SystemMetadata,
    AppChange,
    Mem0GetAll,
)
from dotfiles_maintainer.tools import (
    baseline,
    changes,
    history,
    lifecycle,
    roadmap,
    trials,
    troubleshooting,
)

# --- MemoryManager Coverage ---


@pytest.mark.asyncio
async def test_memory_manager_validation_errors():
    config = ServerConfig()
    with patch("dotfiles_maintainer.core.memory.AsyncMemory") as mock_async_mem:
        client = mock_async_mem.return_value
        manager = MemoryManager(config)

        # add_with_redaction ValidationError
        client.add = AsyncMock(
            side_effect=ValidationError.from_exception_data("test", [])
        )
        res = await manager.add_with_redaction("test")
        assert isinstance(res, Mem0AddResponse)
        assert len(res.results) == 0

        # search ValidationError
        client.search = AsyncMock(
            side_effect=ValidationError.from_exception_data("test", [])
        )
        res = await manager.search("test")
        assert isinstance(res, SearchResult)
        assert len(res.results) == 0

        # update ValidationError
        client.update = AsyncMock(
            side_effect=ValidationError.from_exception_data("test", [])
        )
        with pytest.raises(ValidationError):
            await manager.update("id", "test")


@pytest.mark.asyncio
async def test_memory_manager_get_all_and_delete():
    config = ServerConfig()
    with patch("dotfiles_maintainer.core.memory.AsyncMemory") as mock_async_mem:
        client = mock_async_mem.return_value
        manager = MemoryManager(config)

        # get_all
        client.get_all = AsyncMock(return_value={"results": []})
        res = await manager.get_all()
        assert isinstance(res, Mem0GetAllResponse)

        # get_all error
        client.get_all.side_effect = Exception("error")
        with pytest.raises(Exception):
            await manager.get_all()

        # delete_all
        client.delete_all = AsyncMock(return_value={"message": "deleted"})
        res = await manager.delete_all()
        assert isinstance(res, Mem0DeleteResponse)

        # delete_all error
        client.delete_all.side_effect = Exception("error")
        with pytest.raises(Exception):
            await manager.delete_all()


@pytest.mark.asyncio
async def test_memory_manager_reset():
    config = ServerConfig()
    config.memory_db_path = Path("./test_qdrant")
    config.memory_db_path.mkdir(parents=True, exist_ok=True)

    with patch("dotfiles_maintainer.core.memory.AsyncMemory") as mock_async_mem:
        client = mock_async_mem.return_value
        manager = MemoryManager(config)

        # reset success
        client.reset = AsyncMock()
        await manager.reset()
        assert (
            not config.memory_db_path.exists()
            or list(config.memory_db_path.iterdir()) == []
        )

        # reset error
        client.reset.side_effect = Exception("error")
        with pytest.raises(Exception):
            await manager.reset()

    if config.memory_db_path.exists():
        shutil.rmtree(config.memory_db_path)


# --- Config Coverage ---


def test_config_providers():
    # Test different providers via env vars
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            config = ServerConfig(llm_key="")
            assert config.llm_provider == "openai"
            assert config.llm_key == "sk-test"

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "at-test"}):
            config = ServerConfig(llm_key="")
            assert config.llm_provider == "anthropic"
            assert config.llm_key == "at-test"

        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434"}):
            config = ServerConfig(llm_key="")
            assert config.llm_provider == "ollama"
            assert config.llm_key == "http://localhost:11434"
            assert config.llm_config.provider == "ollama"


def test_config_no_key_warning():
    with patch.dict(os.environ, {}, clear=True):
        with patch("dotfiles_maintainer.config.logger") as mock_logger:
            config = ServerConfig(llm_key="")
            _ = config.llm_config
            mock_logger.warning.assert_called()


# --- Tools Coverage (Error/Empty branches) ---


@pytest.fixture
def mock_system_metadata():
    return SystemMetadata(
        os_version="macOS 14.2",
        main_shell="Zsh",
        main_terminal_emulator="Alacritty",
        main_prompt_engine="starship",
        main_editor="nvim",
        version_control="git",
        package_manager="brew",
        cpu="M2",
        extra="",
    )


@pytest.fixture
def mock_app_config():
    return AppConfig(
        app_name="vim",
        source_path="~/.vimrc",
        destination_path="~/.vimrc",
        file_structure="monolithic",
    )


@pytest.fixture
def mock_app_change():
    return AppChange(
        app_name="vim",
        source_path="~/.vimrc",
        destination_path="~/.vimrc",
        file_structure="monolithic",
        change_type="feat",
        rationale="why",
        improvement_metric="metric",
        description="what",
    )


@pytest.mark.asyncio
async def test_tools_empty_results(
    mock_system_metadata, mock_app_config, mock_app_change
):
    memory = MagicMock()
    memory.add_with_redaction = AsyncMock(return_value=Mem0AddResponse(results=[]))

    # baseline
    res = await baseline.initialize_system_baseline(
        memory, "stow", [], mock_system_metadata
    )
    assert "duplicate detected" in res

    # changes
    res = await changes.commit_contextual_change(memory, mock_app_change)
    assert "duplicate detected" in res

    # history
    res = await history.ingest_version_history(memory, 20, 10)
    assert "not ingested" in res

    # lifecycle
    res = await lifecycle.track_lifecycle_events(
        memory, "DEPRECATE", mock_app_config, None, "logic"
    )
    assert "duplicate detected" in res

    # roadmap
    res = await roadmap.log_conceptual_roadmap(memory, "title", "hypo", "block", "LOW")
    assert "duplicate detected" in res

    # trials
    res = await trials.manage_trial(memory, "name", 7, "criteria")
    assert "duplicate detected" in res

    # troubleshooting
    res = await troubleshooting.log_troubleshooting_event(memory, "sig", "cause", "fix")
    assert "duplicate detected" in res


@pytest.mark.asyncio
async def test_tools_exceptions(mock_system_metadata, mock_app_config, mock_app_change):
    memory = MagicMock()
    memory.add_with_redaction = AsyncMock(side_effect=Exception("boom"))
    memory.search = AsyncMock(side_effect=Exception("boom"))

    assert "Failed" in await baseline.initialize_system_baseline(
        memory, "stow", [], mock_system_metadata
    )
    assert "Failed" in await changes.commit_contextual_change(memory, mock_app_change)
    assert "Error" in await history.ingest_version_history(memory, 20, 10)
    assert "Failed" in await lifecycle.track_lifecycle_events(
        memory, "DEPRECATE", mock_app_config, None, "logic"
    )
    assert "Failed" in await roadmap.log_conceptual_roadmap(
        memory, "title", "hypo", "block", "LOW"
    )
    assert "Failed" in await trials.manage_trial(memory, "name", 7, "criteria")
    assert "Failed" in await troubleshooting.log_troubleshooting_event(
        memory, "sig", "cause", "fix"
    )
