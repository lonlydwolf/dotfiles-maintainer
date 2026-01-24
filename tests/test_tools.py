"""Unit tests for all MCP tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.core.memory import MemoryManager
from dotfiles_maintainer.core.types import (
    AppChange,
    AppConfig,
    DriftResult,
    Mem0AddResponse,
    Mem0Event,
    Mem0UpdateResponse,
    MemoryResult,
    SearchResult,
    SystemMetadata,
)
from dotfiles_maintainer.tools import (
    baseline,
    changes,
    drift,
    history,
    lifecycle,
    queries,
    roadmap,
    trials,
    troubleshooting,
    updates,
)


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock(spec=MemoryManager)
    manager.add_with_redaction = AsyncMock()
    manager.search = AsyncMock()
    manager.update = AsyncMock()
    return manager


# --- Baseline Tools ---


@pytest.mark.asyncio
async def test_initialize_system_baseline_success(mock_memory_manager):
    config_map = [
        AppConfig(
            app_name="vim",
            source_path="~",
            destination_path="~",
            file_structure="monolithic",
            dependencies=[],
        )
    ]
    sys_meta = SystemMetadata(
        os_version="MacOS",
        main_shell="Zsh",
        main_terminal_emulator="iTerm2",
        main_prompt_engine="Starship",
        main_editor="nvim",
        version_control="git",
        package_manager="brew",
        cpu="M1",
        extra="",
    )

    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="baseline", event="ADD")]
    )

    result = await baseline.initialize_system_baseline(
        mock_memory_manager, "stow", config_map, sys_meta
    )

    assert "System Baseline Initialized" in result
    mock_memory_manager.add_with_redaction.assert_called_once()
    call_args = mock_memory_manager.add_with_redaction.call_args
    assert call_args.kwargs["metadata"]["type"] == "baseline"


@pytest.mark.asyncio
async def test_initialize_system_baseline_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Memory Error")

    result = await baseline.initialize_system_baseline(
        mock_memory_manager,
        "stow",
        [],
        {},  # pyright: ignore
    )

    assert "Failed to Initialize Baseline" in result


# --- Changes Tools ---


@pytest.mark.asyncio
async def test_commit_contextual_change_success(mock_memory_manager):
    data = AppChange(
        app_name="zsh",
        change_type="optimization",
        rationale="faster startup",
        improvement_metric="-100ms",
        description="removed plugin",
        vcs_commit_id="abc1234",
        source_path="src",
        destination_path="dest",
        file_structure="monolithic",
        dependencies=[],
    )
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="change", event="ADD")]
    )

    result = await changes.commit_contextual_change(mock_memory_manager, data)

    assert "Change logged to memory" in result
    mock_memory_manager.add_with_redaction.assert_called_once()
    assert "abc1234" in mock_memory_manager.add_with_redaction.call_args[0][0]


# --- Drift Tools ---


@pytest.mark.asyncio
@patch("dotfiles_maintainer.tools.drift.get_vcs_command", new_callable=AsyncMock)
async def test_check_config_drift_git_detected(mock_get_vcs, mock_memory_manager):
    mock_vcs_cmd = MagicMock()
    mock_vcs_cmd.vcs_type = "git"
    mock_vcs_cmd.get_status.return_value = "M .zshrc\n"
    mock_get_vcs.return_value = mock_vcs_cmd

    result = await drift.check_config_drift(mock_memory_manager)

    assert result.status == "modified"
    assert result.vcs_type == "git"
    assert "M .zshrc" in result.message
    mock_memory_manager.add_with_redaction.assert_called_once()


@pytest.mark.asyncio
@patch("dotfiles_maintainer.tools.drift.get_vcs_command", new_callable=AsyncMock)
async def test_check_config_drift_no_drift(mock_get_vcs, mock_memory_manager):
    mock_vcs_cmd = MagicMock()
    mock_vcs_cmd.vcs_type = "git"
    mock_vcs_cmd.get_status.return_value = ""
    mock_get_vcs.return_value = mock_vcs_cmd

    result = await drift.check_config_drift(mock_memory_manager)

    assert result.status == "clean"
    mock_memory_manager.add_with_redaction.assert_not_called()


# --- History Tools ---


@pytest.mark.asyncio
@patch(
    "dotfiles_maintainer.tools.history.detect_vcs_type", new_callable=AsyncMock
)  # Mock where it is imported
@patch("dotfiles_maintainer.tools.history.VCSCommand")
async def test_ingest_version_history_success(
    mock_vcs_cls, mock_detect_vcs, mock_memory_manager
):
    mock_detect_vcs.return_value = "git"
    mock_vcs_instance = mock_vcs_cls.return_value
    mock_vcs_instance.get_log.return_value = "commit 1\ncommit 2"
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="log", event="ADD")]
    )

    result = await history.ingest_version_history(mock_memory_manager, count=5)

    assert "Ingested last 5" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


# --- Lifecycle Tools ---


@pytest.mark.asyncio
async def test_track_lifecycle_events_replace(mock_memory_manager):
    old = AppConfig(
        app_name="vim",
        source_path="",
        destination_path="",
        file_structure="monolithic",
        dependencies=[],
    )
    new = AppConfig(
        app_name="neovim",
        source_path="",
        destination_path="",
        file_structure="monolithic",
        dependencies=[],
    )
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="lifecycle", event="ADD")]
    )

    result = await lifecycle.track_lifecycle_events(
        mock_memory_manager, "REPLACE", old, new, "better lsp"
    )

    assert "Lifecycle event logged" in result
    assert "REPLACE" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


# --- Queries Tools ---


@pytest.mark.asyncio
async def test_get_config_context_success(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="mem1", score=1.0)]
    )

    result = await queries.get_config_context(mock_memory_manager, "zsh")

    assert len(result) == 1
    assert result[0].memory == "mem1"
    mock_memory_manager.search.assert_called_once_with("zsh")


@pytest.mark.asyncio
async def test_get_config_context_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search Error")
    result = await queries.get_config_context(mock_memory_manager, "zsh")
    assert result == []


@pytest.mark.asyncio
async def test_search_change_history(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="found change", score=1.0)]
    )

    result = await queries.search_change_history(mock_memory_manager, "latency", "zsh")

    assert len(result) == 1
    assert result[0].memory == "found change"
    mock_memory_manager.search.assert_called_once_with("zsh: latency")


@pytest.mark.asyncio
async def test_search_change_history_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search Error")
    result = await queries.search_change_history(mock_memory_manager, "latency", "zsh")
    assert result == []


@pytest.mark.asyncio
async def test_check_system_dependencies(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="depends on fzf", score=1.0)]
    )

    result = await queries.check_system_dependencies(mock_memory_manager, "telescope")

    assert len(result) == 1
    assert result[0].memory == "depends on fzf"
    mock_memory_manager.search.assert_called_once_with("telescope")


@pytest.mark.asyncio
async def test_check_system_dependencies_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search Error")
    result = await queries.check_system_dependencies(mock_memory_manager, "telescope")
    assert result == []


@pytest.mark.asyncio
async def test_sync_work_in_progress(mock_memory_manager):
    conf = AppConfig(
        app_name="tmux",
        source_path="",
        destination_path="",
        file_structure="monolithic",
        dependencies=[],
    )

    result = await queries.sync_work_in_progress(
        mock_memory_manager, "fix layout", [conf], "confusing syntax"
    )

    assert "WIP synchronized" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


@pytest.mark.asyncio
async def test_sync_work_in_progress_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add Error")
    conf = AppConfig(
        app_name="tmux",
        source_path="",
        destination_path="",
        file_structure="monolithic",
        dependencies=[],
    )
    result = await queries.sync_work_in_progress(
        mock_memory_manager, "fix layout", [conf], "confusing syntax"
    )
    assert "Failed synchronize WIP" in result


# --- Roadmap Tools ---


@pytest.mark.asyncio
async def test_log_conceptual_roadmap(mock_memory_manager):
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="roadmap", event="ADD")]
    )
    result = await roadmap.log_conceptual_roadmap(
        mock_memory_manager, "idea", "hypothesis", "blocker", "HIGH"
    )

    assert "Roadmap logged" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


@pytest.mark.asyncio
async def test_query_roadmap(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="idea 1", score=1.0)]
    )

    result = await roadmap.query_roadmap(mock_memory_manager, "pending", "HIGH")

    assert len(result) == 1
    assert result[0].memory == "idea 1"
    mock_memory_manager.search.assert_called_once_with("roadmap pending HIGH priority")


# --- Trials Tools ---


@pytest.mark.asyncio
async def test_manage_trial(mock_memory_manager):
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="trial", event="ADD")]
    )
    result = await trials.manage_trial(mock_memory_manager, "plugin-x", 7, "works well")

    assert "Trial Started" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


@pytest.mark.asyncio
async def test_list_active_trials(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="trial 1", score=1.0)]
    )

    result = await trials.list_active_trials(mock_memory_manager, 3)

    assert len(result) == 1
    assert result[0].memory == "trial 1"
    mock_memory_manager.search.assert_called_once_with("active plugin trials")


# --- Troubleshooting Tools ---


@pytest.mark.asyncio
async def test_log_troubleshooting_event(mock_memory_manager):
    mock_memory_manager.add_with_redaction.return_value = Mem0AddResponse(
        results=[Mem0Event(id="1", memory="troubleshooting", event="ADD")]
    )
    result = await troubleshooting.log_troubleshooting_event(
        mock_memory_manager, "error", "cause", "fix"
    )

    assert "Troubleshooting Knowledge logged" in result
    mock_memory_manager.add_with_redaction.assert_called_once()


@pytest.mark.asyncio
async def test_get_troubleshooting_guide(mock_memory_manager):
    mock_memory_manager.search.return_value = SearchResult(
        results=[MemoryResult(id="1", memory="solution", score=1.0)]
    )

    result = await troubleshooting.get_troubleshooting_guide(
        mock_memory_manager, "error"
    )

    assert len(result) == 1
    assert result[0].memory == "solution"
    mock_memory_manager.search.assert_called_once_with("troubleshooting error")


# --- Updates Tools ---


@pytest.mark.asyncio
async def test_update_memory_success(mock_memory_manager):
    mock_memory_manager.update.return_value = Mem0UpdateResponse(
        id="id-1", text="new text"
    )
    result = await updates.update_memory(mock_memory_manager, "id-1", "new text")

    assert "updated successfully" in result.message
    mock_memory_manager.update.assert_called_once_with("id-1", "new text")


@pytest.mark.asyncio
async def test_update_memory_failure(mock_memory_manager):
    mock_memory_manager.update.side_effect = Exception("Update Failed")
    result = await updates.update_memory(mock_memory_manager, "id-1", "new text")
    assert "Error updating memory" in result.message


@pytest.mark.asyncio
async def test_commit_contextual_change_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add error")

    result = await changes.commit_contextual_change(mock_memory_manager, MagicMock())

    assert "Failed to log change to memory: Add error" in result


@pytest.mark.asyncio
@patch("dotfiles_maintainer.tools.drift.get_vcs_command", new_callable=AsyncMock)
async def test_check_config_drift_failure(mock_get_vcs, mock_memory_manager):
    mock_get_vcs.side_effect = Exception("VCS error")

    result = await drift.check_config_drift(mock_memory_manager)

    assert result.status == "error"

    assert "VCS error" in result.message


@pytest.mark.asyncio
@patch("dotfiles_maintainer.tools.history.detect_vcs_type", new_callable=AsyncMock)
async def test_ingest_version_history_failure(mock_detect_vcs, mock_memory_manager):
    mock_detect_vcs.side_effect = Exception("VCS error")

    result = await history.ingest_version_history(mock_memory_manager)

    assert "Error ingesting history: VCS error" in result


@pytest.mark.asyncio
async def test_track_lifecycle_events_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add error")

    result = await lifecycle.track_lifecycle_events(
        mock_memory_manager, "DEPRECATE", MagicMock(), None, "logic"
    )

    assert "Failed to log Lifecycle Event: Add error" in result


@pytest.mark.asyncio
async def test_log_conceptual_roadmap_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add error")

    result = await roadmap.log_conceptual_roadmap(
        mock_memory_manager, "idea", "hyp", "block", "LOW"
    )

    assert "Failed to save Roadmap Entry: Add error" in result


@pytest.mark.asyncio
async def test_query_roadmap_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search error")

    result = await roadmap.query_roadmap(mock_memory_manager, "pending", "HIGH")

    assert result == []


@pytest.mark.asyncio
async def test_manage_trial_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add error")

    result = await trials.manage_trial(mock_memory_manager, "name", 1, "crit")

    assert "Failed to set Trial for name: Add error" in result


@pytest.mark.asyncio
async def test_list_active_trials_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search error")

    result = await trials.list_active_trials(mock_memory_manager, 1)

    assert result == []


@pytest.mark.asyncio
async def test_log_troubleshooting_event_failure(mock_memory_manager):
    mock_memory_manager.add_with_redaction.side_effect = Exception("Add error")

    result = await troubleshooting.log_troubleshooting_event(
        mock_memory_manager, "err", "cause", "fix"
    )

    assert "Failed to add err troubleshooting to memory: Add error" in result


@pytest.mark.asyncio
async def test_get_troubleshooting_guide_failure(mock_memory_manager):
    mock_memory_manager.search.side_effect = Exception("Search error")

    result = await troubleshooting.get_troubleshooting_guide(mock_memory_manager, "err")

    assert result == []
