"""Tests for the MCP server and tool registration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.core.memory import MemoryManager
from dotfiles_maintainer.server import (
    get_config_context,
    get_memory,
    health_check,
    initialize_system_baseline,
    mcp,
)


@pytest.fixture
def mock_ctx():
    """Mock MCP context with lifespan context."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context.memory = MagicMock(spec=MemoryManager)
    ctx.request_context.lifespan_context.config = MagicMock()
    return ctx


@pytest.mark.asyncio
async def test_get_memory(mock_ctx):
    """Test memory extraction from context."""
    memory = get_memory(mock_ctx)
    assert memory == mock_ctx.request_context.lifespan_context.memory


@pytest.mark.asyncio
async def test_initialize_system_baseline_tool(mock_ctx):
    """Test initialize_system_baseline tool registration call."""
    with patch(
        "dotfiles_maintainer.tools.baseline.initialize_system_baseline",
        new_callable=AsyncMock,
    ) as mock_impl:
        await initialize_system_baseline(mock_ctx, "stow", [], {})  # pyright: ignore
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_get_config_context_tool(mock_ctx):
    """Test get_config_context tool registration call."""
    with patch(
        "dotfiles_maintainer.tools.queries.get_config_context", new_callable=AsyncMock
    ) as mock_impl:
        await get_config_context(mock_ctx, "zsh")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_tool(mock_ctx):
    """Test health_check tool registration call."""
    with patch(
        "dotfiles_maintainer.tools.health.health_check", new_callable=AsyncMock
    ) as mock_impl:
        await health_check(mock_ctx)
        mock_impl.assert_called_once()


# Add a few more to cover server.py lines
@pytest.mark.asyncio
async def test_commit_contextual_change_tool(mock_ctx):
    from dotfiles_maintainer.server import commit_contextual_change

    with patch(
        "dotfiles_maintainer.tools.changes.commit_contextual_change",
        new_callable=AsyncMock,
    ) as mock_impl:
        await commit_contextual_change(mock_ctx, MagicMock())
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_check_config_drift_tool(mock_ctx):
    from dotfiles_maintainer.server import check_config_drift

    with patch(
        "dotfiles_maintainer.tools.drift.check_config_drift", new_callable=AsyncMock
    ) as mock_impl:
        await check_config_drift(mock_ctx)
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_version_history_tool(mock_ctx):
    from dotfiles_maintainer.server import ingest_version_history

    with patch(
        "dotfiles_maintainer.tools.history.ingest_version_history",
        new_callable=AsyncMock,
    ) as mock_impl:
        await ingest_version_history(mock_ctx, 10)
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_track_lifecycle_events_tool(mock_ctx):
    from dotfiles_maintainer.server import track_lifecycle_events

    with patch(
        "dotfiles_maintainer.tools.lifecycle.track_lifecycle_events",
        new_callable=AsyncMock,
    ) as mock_impl:
        await track_lifecycle_events(
            mock_ctx, "REPLACE", MagicMock(), MagicMock(), "logic"
        )
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_log_conceptual_roadmap_tool(mock_ctx):
    from dotfiles_maintainer.server import log_conceptual_roadmap

    with patch(
        "dotfiles_maintainer.tools.roadmap.log_conceptual_roadmap",
        new_callable=AsyncMock,
    ) as mock_impl:
        await log_conceptual_roadmap(mock_ctx, "idea", "hypo", "block", "HIGH")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_query_roadmap_tool(mock_ctx):
    from dotfiles_maintainer.server import query_roadmap

    with patch(
        "dotfiles_maintainer.tools.roadmap.query_roadmap", new_callable=AsyncMock
    ) as mock_impl:
        await query_roadmap(mock_ctx, "pending", "HIGH")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_manage_trial_tool(mock_ctx):
    from dotfiles_maintainer.server import manage_trial

    with patch(
        "dotfiles_maintainer.tools.trials.manage_trial", new_callable=AsyncMock
    ) as mock_impl:
        await manage_trial(mock_ctx, "name", 7, "criteria")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_list_active_trials_tool(mock_ctx):
    from dotfiles_maintainer.server import list_active_trials

    with patch(
        "dotfiles_maintainer.tools.trials.list_active_trials", new_callable=AsyncMock
    ) as mock_impl:
        await list_active_trials(mock_ctx, 5)
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_log_troubleshooting_event_tool(mock_ctx):
    from dotfiles_maintainer.server import log_troubleshooting_event

    with patch(
        "dotfiles_maintainer.tools.troubleshooting.log_troubleshooting_event",
        new_callable=AsyncMock,
    ) as mock_impl:
        await log_troubleshooting_event(mock_ctx, "err", "cause", "fix")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_get_troubleshooting_guide_tool(mock_ctx):
    from dotfiles_maintainer.server import get_troubleshooting_guide

    with patch(
        "dotfiles_maintainer.tools.troubleshooting.get_troubleshooting_guide",
        new_callable=AsyncMock,
    ) as mock_impl:
        await get_troubleshooting_guide(mock_ctx, "err")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_search_change_history_tool(mock_ctx):
    from dotfiles_maintainer.server import search_change_history

    with patch(
        "dotfiles_maintainer.tools.queries.search_change_history",
        new_callable=AsyncMock,
    ) as mock_impl:
        await search_change_history(mock_ctx, "query")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_check_system_dependencies_tool(mock_ctx):
    from dotfiles_maintainer.server import check_system_dependencies

    with patch(
        "dotfiles_maintainer.tools.queries.check_system_dependencies",
        new_callable=AsyncMock,
    ) as mock_impl:
        await check_system_dependencies(mock_ctx, "tool")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_update_memory_tool(mock_ctx):
    from dotfiles_maintainer.server import update_memory

    with patch(
        "dotfiles_maintainer.tools.updates.update_memory", new_callable=AsyncMock
    ) as mock_impl:
        await update_memory(mock_ctx, "id", "text")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_sync_work_in_progress_tool(mock_ctx):
    from dotfiles_maintainer.server import sync_work_in_progress

    with patch(
        "dotfiles_maintainer.tools.queries.sync_work_in_progress",
        new_callable=AsyncMock,
    ) as mock_impl:
        await sync_work_in_progress(mock_ctx, "goal", [], "struggle")
        mock_impl.assert_called_once()


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test the app lifespan context manager."""
    from dotfiles_maintainer.server import app_lifespan

    mock_server = MagicMock()
    async with app_lifespan(mock_server) as context:
        assert context.config is not None
        assert context.memory is not None


def test_main():
    """Test the main entry point."""
    from dotfiles_maintainer.server import main

    with patch.object(mcp, "run") as mock_run:
        with patch("dotfiles_maintainer.server.__name__", "__main__"):
            # This doesn't actually trigger the if __name__ == "__main__" block
            # but we can call main directly
            main()
            mock_run.assert_called_once()
