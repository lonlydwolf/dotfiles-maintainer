"""Integration tests for the CLI entry point."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.cli import app, shutdown_loop
from dotfiles_maintainer.core.types import (
    DriftResult,
    HealthStatus,
    SearchResult,
    Mem0GetAllResponse,
    MemoryResult,
    Mem0GetAll,
)
from typer.testing import CliRunner

runner = CliRunner()


@patch("dotfiles_maintainer.cli.get_memory")
@patch("dotfiles_maintainer.tools.drift.check_config_drift", new_callable=AsyncMock)
def test_cli_system_drift(mock_drift, mock_get_memory):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm

    # Clean
    mock_drift.return_value = DriftResult(
        status="clean",
        vcs_type="git",
        modified_files=[],
        total_changes=0,
        message="No drift detected",
    )
    result = runner.invoke(app, ["system", "drift"])
    assert result.exit_code == 0
    assert "System is in sync." in result.stdout

    # Modified
    mock_drift.return_value = DriftResult(
        status="modified",
        vcs_type="git",
        modified_files=["file1"],
        total_changes=1,
        message="Drift detected",
    )
    result = runner.invoke(app, ["system", "drift"])
    assert result.exit_code == 0
    assert "Drift Detected:" in result.stdout

    # Error
    mock_drift.return_value = DriftResult(
        status="error",
        vcs_type="git",
        modified_files=[],
        total_changes=0,
        message="Error",
    )
    result = runner.invoke(app, ["system", "drift"])
    assert result.exit_code == 0
    assert "Status: Error" in result.stdout


@patch("dotfiles_maintainer.cli.get_memory")
@patch("dotfiles_maintainer.tools.health.health_check", new_callable=AsyncMock)
def test_cli_system_health(mock_health, mock_get_memory):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm
    mock_health.return_value = HealthStatus(
        status="healthy",
        version="1.0.0",
        components={
            "memory": "connected",
            "vcs": "active (git)",
            "llm_provider": "configured (google)",
        },
    )
    result = runner.invoke(app, ["system", "health"])
    assert result.exit_code == 0
    assert "Checking system health..." in result.stdout
    assert "healthy" in result.stdout

    # Unhealthy
    mock_health.side_effect = Exception("boom")
    result = runner.invoke(app, ["system", "health"])
    assert result.exit_code == 0
    assert "Error: boom" in result.stdout


@patch("dotfiles_maintainer.cli.get_memory")
def test_cli_memory_inspect(mock_get_memory):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm

    # Results
    mock_mm.search = AsyncMock(
        return_value=SearchResult(
            results=[MemoryResult(id="1", memory="mem1", score=0.9)]
        )
    )
    result = runner.invoke(app, ["memory", "inspect", "vim"])
    assert result.exit_code == 0
    assert "mem1" in result.stdout

    # No results
    mock_mm.search = AsyncMock(return_value=SearchResult(results=[]))
    result = runner.invoke(app, ["memory", "inspect", "vim"])
    assert result.exit_code == 0
    assert "No matching memories found." in result.stdout

    # Error
    mock_mm.search.side_effect = Exception("boom")
    result = runner.invoke(app, ["memory", "inspect", "vim"])
    assert result.exit_code == 0
    assert "Error: boom" in result.stdout


@patch("dotfiles_maintainer.cli.get_memory")
def test_cli_memory_facts(mock_get_memory):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm

    # Results
    mock_mm.get_all = AsyncMock(
        return_value=Mem0GetAllResponse(results=[Mem0GetAll(id="1", memory="fact1")])
    )
    result = runner.invoke(app, ["memory", "facts"])
    assert result.exit_code == 0
    assert "fact1" in result.stdout

    # No results
    mock_mm.get_all = AsyncMock(return_value=Mem0GetAllResponse(results=[]))
    result = runner.invoke(app, ["memory", "facts"])
    assert result.exit_code == 0
    assert "No memories found." in result.stdout

    # Error
    mock_mm.get_all.side_effect = Exception("boom")
    result = runner.invoke(app, ["memory", "facts"])
    assert result.exit_code == 0
    assert "Error: boom" in result.stdout


@patch("dotfiles_maintainer.cli.get_memory")
def test_cli_memory_clear(mock_get_memory):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm
    mock_mm.reset = AsyncMock()

    # Test with confirmation
    result = runner.invoke(app, ["memory", "clear"], input="y\n")
    assert result.exit_code == 0
    assert "Memory reset successfully." in result.stdout

    # Test cancellation
    result = runner.invoke(app, ["memory", "clear"], input="n\n")
    assert result.exit_code == 0
    assert "Operation cancelled." in result.stdout

    # Test error
    mock_mm.reset.side_effect = Exception("boom")
    result = runner.invoke(app, ["memory", "clear"], input="y\n")
    assert result.exit_code == 0
    assert "Error: boom" in result.stdout


def test_cli_config_show():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "Config Source:" in result.stdout


def test_cli_config_path():
    result = runner.invoke(app, ["config", "path"])
    assert result.exit_code == 0
    assert "Working Directory:" in result.stdout


def test_cli_system_info():
    result = runner.invoke(app, ["system", "info"])
    assert result.exit_code == 0
    assert "System Info" in result.stdout


@patch("dotfiles_maintainer.cli.mcp")
def test_cli_tools_list(mock_mcp):
    mock_tool_mgr = MagicMock()
    mock_mcp._tool_manager = mock_tool_mgr
    mock_tool = MagicMock()
    mock_tool.description = "Test tool"
    mock_tool_mgr._tools = {"test_tool": mock_tool}

    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "test_tool" in result.stdout

    # Fallback
    mock_mcp._tool_manager = None
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "Could not access tool registry directly." in result.stdout

    # Error
    # To trigger the exception, we can make _tool_manager a property that raises
    type(mock_mcp)._tool_manager = property(
        lambda x: (_ for _ in ()).throw(Exception("boom"))
    )
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "Error listing tools:" in result.stdout


def test_cli_get_memory():
    from dotfiles_maintainer.cli import get_memory

    with patch("dotfiles_maintainer.cli.MemoryManager") as mock_mm:
        manager = get_memory()
        assert manager == mock_mm.return_value


@patch("dotfiles_maintainer.cli.MemoryManager")
@patch("dotfiles_maintainer.cli.get_memory")
@patch("dotfiles_maintainer.cli.mcp")
def test_cli_tools_run(mock_mcp, mock_get_memory, mock_mm_class):
    mock_mm = MagicMock()
    mock_get_memory.return_value = mock_mm
    mock_mm_class.return_value = mock_mm

    mock_tool_mgr = MagicMock()
    mock_mcp._tool_manager = mock_tool_mgr
    mock_tool = MagicMock()
    mock_tool.fn = AsyncMock(
        return_value={"status": "success", "nested": {"key": "val"}}
    )
    mock_tool_mgr._tools = {"test_tool": mock_tool}

    # Success with recursion in serialize_result and ignored arg
    result = runner.invoke(
        app, ["tools", "run", "test_tool", "arg1=val1", "ignored_arg"]
    )
    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout
    assert "Ignored argument 'ignored_arg'" in result.stdout

    # Test serialize_result with Pydantic model
    mock_model = MagicMock()
    mock_model.model_dump.return_value = {"dumped": "data"}
    mock_tool.fn.return_value = [mock_model]
    result = runner.invoke(app, ["tools", "run", "test_tool", "arg1=val1"])
    assert result.exit_code == 0
    assert '"dumped": "data"' in result.stdout

    # Tool not found
    result = runner.invoke(app, ["tools", "run", "nonexistent"])
    assert result.exit_code == 0
    assert "Tool 'nonexistent' not found." in result.stdout

    # Registry missing
    mock_mcp._tool_manager = None
    result = runner.invoke(app, ["tools", "run", "test_tool"])
    assert result.exit_code == 0
    assert "Could not access tool registry." in result.stdout

    # TypeError
    mock_mcp._tool_manager = mock_tool_mgr
    mock_tool.fn.side_effect = TypeError("wrong args")
    result = runner.invoke(app, ["tools", "run", "test_tool"])
    assert result.exit_code == 0
    assert "Argument Error:" in result.stdout

    # Exception
    mock_tool.fn.side_effect = Exception("boom")
    result = runner.invoke(app, ["tools", "run", "test_tool"])
    assert result.exit_code == 0
    assert "Execution Error: boom" in result.stdout


def test_cli_shutdown_loop():
    with patch("asyncio.all_tasks") as mock_tasks:
        mock_task = MagicMock()
        mock_tasks.return_value = {mock_task}
        with patch("asyncio.gather", new_callable=AsyncMock):
            shutdown_loop()
            mock_task.cancel.assert_called()


def test_cli_mock_context():
    from dotfiles_maintainer.cli import MockContext, MockRequest, MockLifespan

    ctx = MockContext(
        request_context=MockRequest(
            lifespan_context=MockLifespan(config=MagicMock(), memory=MagicMock())
        )
    )
    with patch("logging.info") as mock_info:
        ctx.info("test")
        mock_info.assert_called_with("test")
    with patch("logging.error") as mock_error:
        ctx.error("test")
        mock_error.assert_called_with("test")
    with patch("logging.warning") as mock_warning:
        ctx.warning("test")
        mock_warning.assert_called_with("test")
    with patch("logging.debug") as mock_debug:
        ctx.debug("test")
        mock_debug.assert_called_with("test")
