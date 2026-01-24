"""Tests for VCS utilities."""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.core.types import MemoryResult, SearchResult
from dotfiles_maintainer.utils.vcs import (
    VCSCommand,
    detect_vcs_from_filesystem,
    detect_vcs_from_memory,
    detect_vcs_type,
    get_repo_root,
    get_vcs_command,
    get_vcs_type_cached,
    is_in_repo,
    validate_vcs_installed,
)

# --- VCS Detection Tests ---


def test_detect_vcs_from_filesystem_git(tmp_path):
    (tmp_path / ".git").mkdir()
    assert detect_vcs_from_filesystem(tmp_path) == "git"


def test_detect_vcs_from_filesystem_jj(tmp_path):
    (tmp_path / ".jj").mkdir()
    assert detect_vcs_from_filesystem(tmp_path) == "jj"


def test_detect_vcs_from_filesystem_none(tmp_path):
    assert detect_vcs_from_filesystem(tmp_path) is None


def test_detect_vcs_from_filesystem_nested(tmp_path):
    (tmp_path / ".git").mkdir()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    assert detect_vcs_from_filesystem(subdir) == "git"


def test_get_vcs_type_cached(tmp_path):
    (tmp_path / ".git").mkdir()
    assert get_vcs_type_cached(str(tmp_path)) == "git"
    # Should be cached
    assert get_vcs_type_cached(str(tmp_path)) == "git"


@pytest.mark.asyncio
async def test_detect_vcs_from_memory_success():
    with patch("dotfiles_maintainer.core.memory.MemoryManager") as MockMemoryManager:
        mock_instance = MockMemoryManager.return_value
        # Mocking search to return a SearchResult
        mock_instance.search = AsyncMock(
            return_value=SearchResult(
                results=[
                    MemoryResult(id="1", memory="version_control: 'jj'", score=1.0)
                ]
            )
        )

        # Also need to mock ServerConfig inside detect_vcs_from_memory
        with patch("dotfiles_maintainer.config.ServerConfig"):
            vcs = await detect_vcs_from_memory()
            assert vcs == "jj"


@pytest.mark.asyncio
async def test_detect_vcs_from_memory_none():
    with patch("dotfiles_maintainer.core.memory.MemoryManager") as MockMemoryManager:
        mock_instance = MockMemoryManager.return_value
        mock_instance.search = AsyncMock(return_value=SearchResult(results=[]))

        with patch("dotfiles_maintainer.config.ServerConfig"):
            vcs = await detect_vcs_from_memory()
            assert vcs is None


@pytest.mark.asyncio
async def test_detect_vcs_from_memory_git():
    with patch("dotfiles_maintainer.core.memory.MemoryManager") as MockMemoryManager:
        mock_instance = MockMemoryManager.return_value
        mock_instance.search = AsyncMock(
            return_value=SearchResult(
                results=[
                    MemoryResult(id="1", memory="version_control: 'git'", score=1.0)
                ]
            )
        )

        with patch("dotfiles_maintainer.config.ServerConfig"):
            vcs = await detect_vcs_from_memory()
            assert vcs == "git"


@pytest.mark.asyncio
async def test_detect_vcs_from_memory_unparseable():
    with patch("dotfiles_maintainer.core.memory.MemoryManager") as MockMemoryManager:
        mock_instance = MockMemoryManager.return_value
        mock_instance.search = AsyncMock(
            return_value=SearchResult(
                results=[MemoryResult(id="1", memory="unknown content", score=1.0)]
            )
        )

        with patch("dotfiles_maintainer.config.ServerConfig"):
            vcs = await detect_vcs_from_memory()
            assert vcs is None


@pytest.mark.asyncio
async def test_detect_vcs_from_memory_exception():
    with patch(
        "dotfiles_maintainer.core.memory.MemoryManager",
        side_effect=Exception("DB error"),
    ):
        vcs = await detect_vcs_from_memory()
        assert vcs is None


@pytest.mark.asyncio
async def test_detect_vcs_type_memory_success(tmp_path):
    # FS check returns None, Memory returns 'jj'
    with patch(
        "dotfiles_maintainer.utils.vcs.detect_vcs_from_filesystem", return_value=None
    ):
        with patch(
            "dotfiles_maintainer.utils.vcs.detect_vcs_from_memory", return_value="jj"
        ):
            vcs = await detect_vcs_type(tmp_path)
            assert vcs == "jj"


@pytest.mark.asyncio
async def test_detect_vcs_type_default(tmp_path):
    # FS check returns None, Memory returns None
    with patch(
        "dotfiles_maintainer.utils.vcs.detect_vcs_from_filesystem", return_value=None
    ):
        with patch(
            "dotfiles_maintainer.utils.vcs.detect_vcs_from_memory", return_value=None
        ):
            vcs = await detect_vcs_type(tmp_path)
            assert vcs == "git"


@pytest.mark.asyncio
async def test_detect_vcs_type_fs_fallback(tmp_path):
    # FS check returns None
    with patch(
        "dotfiles_maintainer.utils.vcs.detect_vcs_from_filesystem", return_value=None
    ):
        # Memory check returns 'git'
        with patch(
            "dotfiles_maintainer.utils.vcs.detect_vcs_from_memory", return_value="git"
        ):
            vcs = await detect_vcs_type(tmp_path)
            assert vcs == "git"


# --- VCS Command Tests ---


def test_vcs_command_git_run():
    vcs = VCSCommand("git")

    with patch("subprocess.check_output") as mock_run:
        mock_run.return_value = "output"  # check_output returns str if text=True

        assert vcs.run(["status"]) == "output"

        mock_run.assert_called_with(
            ["git", "status"], stderr=subprocess.STDOUT, timeout=10, cwd=None, text=True
        )


def test_vcs_command_jj_run():
    vcs = VCSCommand("jj")

    with patch("subprocess.check_output") as mock_run:
        mock_run.return_value = "output"

        assert vcs.run(["st"]) == "output"

        mock_run.assert_called_with(
            ["jj", "st"], stderr=subprocess.STDOUT, timeout=10, cwd=None, text=True
        )


def test_vcs_command_error():
    vcs = VCSCommand("git")
    with patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(1, "git", output="error"),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            vcs.run(["status"])


def test_vcs_command_run_timeout_exception():
    vcs = VCSCommand("git")
    with patch(
        "subprocess.check_output", side_effect=subprocess.TimeoutExpired("git", 5)
    ):
        with pytest.raises(subprocess.TimeoutExpired):
            vcs.run(["status"])


def test_vcs_get_status_git():
    vcs = VCSCommand("git")
    with patch.object(vcs, "run", return_value="M file") as mock_run:
        assert vcs.get_status() == "M file"
        mock_run.assert_called_with(["status", "--short"])


def test_vcs_get_status_jj():
    vcs = VCSCommand("jj")
    with patch.object(vcs, "run", return_value="M file") as mock_run:
        assert vcs.get_status() == "M file"
        mock_run.assert_called_with(["st", "--no-pager"])


def test_vcs_get_log_git():
    vcs = VCSCommand("git")
    with patch.object(vcs, "run", return_value="log") as mock_run:
        vcs.get_log(5)
        mock_run.assert_called()
        assert "log" in mock_run.call_args[0][0]


def test_vcs_get_log_jj():
    vcs = VCSCommand("jj")
    with patch.object(vcs, "run", return_value="log") as mock_run:
        vcs.get_log(5)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "log" in args
        assert "-n" in args
        assert "5" in args
        assert "-T" in args


def test_vcs_get_current_commit_git():
    vcs = VCSCommand("git")
    with patch.object(vcs, "run", return_value="hash\n") as mock_run:
        assert vcs.get_current_commit() == "hash"
        mock_run.assert_called_with(["rev-parse", "HEAD"])


def test_vcs_get_current_commit_jj():
    vcs = VCSCommand("jj")
    with patch.object(vcs, "run", return_value="hash\n") as mock_run:
        assert vcs.get_current_commit() == "hash"
        mock_run.assert_called_with(["log", "-r", "@", "--no-graph", "-T", "commit_id"])


# --- High Level Helpers ---


@pytest.mark.asyncio
async def test_get_vcs_command(tmp_path):
    with patch("dotfiles_maintainer.utils.vcs.detect_vcs_type", return_value="git"):
        cmd = await get_vcs_command(tmp_path)
        assert cmd.vcs_type == "git"


def test_is_in_repo(tmp_path):
    (tmp_path / ".git").mkdir()
    assert is_in_repo(tmp_path) is True
    # If the function works correctly by walking up, this should be True
    # detect_vcs_from_filesystem(tmp_path / "subdir") should find .git in tmp_path
    assert is_in_repo(tmp_path / "subdir") is True

    assert is_in_repo(Path("/tmp")) is False  # Likely False unless /tmp is a repo


def test_get_repo_root(tmp_path):
    (tmp_path / ".git").mkdir()
    assert get_repo_root(tmp_path) == tmp_path.resolve()
    # Should find root from subdir
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    assert get_repo_root(subdir) == tmp_path.resolve()
    assert get_repo_root(Path("/tmp")) is None


def test_get_vcs_type_cached_default():
    with patch(
        "dotfiles_maintainer.utils.vcs.detect_vcs_from_filesystem", return_value=None
    ):
        # Clear cache for this test if needed, but here we just want to see it returns 'git'
        get_vcs_type_cached.cache_clear()
        assert get_vcs_type_cached("/non/existent") == "git"


def test_detect_vcs_from_filesystem_root():
    # Test hitting root directory (current.parent == current)
    root = Path("/")
    assert detect_vcs_from_filesystem(root) is None


@pytest.mark.asyncio
async def test_get_vcs_command_path(tmp_path):
    with patch("dotfiles_maintainer.utils.vcs.detect_vcs_type", return_value="git"):
        cmd = await get_vcs_command(tmp_path)
        assert isinstance(cmd, VCSCommand)
        assert cmd.vcs_type == "git"


def test_validate_vcs_installed():
    with patch("subprocess.run"):
        assert validate_vcs_installed("git") is True

    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert validate_vcs_installed("jj") is False

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
        assert validate_vcs_installed("git") is False

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
        assert validate_vcs_installed("git") is False
