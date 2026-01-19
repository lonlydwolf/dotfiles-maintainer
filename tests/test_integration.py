"""Integration tests for dotfiles-maintainer."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotfiles_maintainer.server import mcp
from dotfiles_maintainer.utils.vcs import VCSCommand


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository."""
    repo_path = tmp_path / "git_repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )
    (repo_path / "file.txt").write_text("initial content")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_path, check=True)
    return repo_path


@pytest.fixture
def jj_repo(tmp_path: Path) -> Path:
    """Create a temporary jj repository."""
    repo_path = tmp_path / "jj_repo"
    repo_path.mkdir()
    # Check if jj is installed
    try:
        subprocess.run(["jj", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("jj is not installed")

    subprocess.run(["jj", "git", "init"], cwd=repo_path, check=True)
    (repo_path / "file.txt").write_text("initial content")
    return repo_path


def test_vcs_command_git_integration(git_repo: Path):
    """Test VCSCommand with a real git repository."""
    vcs = VCSCommand("git", cwd=git_repo)

    # Test get_status
    status = vcs.get_status()
    assert status == ""  # Clean repo

    # Modify file
    (git_repo / "file.txt").write_text("modified content")
    status = vcs.get_status()
    assert "file.txt" in status

    # Test get_current_commit
    commit = vcs.get_current_commit()
    assert len(commit) >= 7


def test_vcs_command_jj_integration(jj_repo: Path):
    """Test VCSCommand with a real jj repository."""
    vcs = VCSCommand("jj", cwd=jj_repo)

    # Test get_status
    status = vcs.get_status()
    assert "file.txt" in status

    # Test get_current_commit
    commit = vcs.get_current_commit()
    assert commit is not None
    assert len(commit) > 0


@pytest.mark.asyncio
async def test_server_tool_registration():
    """Verify that all expected tools are registered with FastMCP."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "initialize_system_baseline",
        "commit_contextual_change",
        "check_config_drift",
        "ingest_version_history",
        "track_lifecycle_events",
        "log_conceptual_roadmap",
        "query_roadmap",
        "manage_trial",
        "list_active_trials",
        "log_troubleshooting_event",
        "get_troubleshooting_guide",
        "get_config_context",
        "search_change_history",
        "check_system_dependencies",
        "update_memory",
        "sync_work_in_progress",
        "health_check",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Tool {expected} not registered"


@pytest.mark.asyncio
async def test_server_lifespan_integration():
    """Test the app lifespan initialization logic."""
    from dotfiles_maintainer.server import app_lifespan

    mock_server = MagicMock()
    # Use a temporary directory for qdrant to avoid side effects
    with pytest.MonkeyPatch().context() as mp:
        test_path = "/tmp/dotfiles-test-qdrant"
        mp.setenv("DOTFILES_MEMORY_PATH", test_path)
        with patch("dotfiles_maintainer.server.MemoryManager") as MockMemoryManager:
            async with app_lifespan(mock_server) as context:
                assert context.config is not None
                assert context.memory is not None
                # Resolve both paths to handle /private/tmp on macOS
                assert context.config.memory_db_path.resolve() == Path(test_path).resolve()
                MockMemoryManager.assert_called_once()
