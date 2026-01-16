"""Version control system utilities.

This module provides VCS detection and command execution helpers.
Prioritizes filesystem checks (fast) over memory queries (slower).
"""

import logging
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

VCSType = Literal["git", "jj"]


# --- VCS Detection (Fast Path: Filesystem) ---


def detect_vcs_from_filesystem(start_path: Path | None = None) -> VCSType | None:
    """Detect VCS type by checking for .git or .jj directories.

    This is the FAST PATH - checks filesystem directly without memory queries.
    Walks up the directory tree until it finds a VCS marker or hits root.

    Args:
        start_path: Directory to start searching from (default: current working directory)

    Returns:
        "git" if .git directory found
        "jj" if .jj directory found
        None if no VCS found

    Performance:
        - Typical: 1-5ms (filesystem stat calls)
        - Cached after first call per session

    Example:
        >>> detect_vcs_from_filesystem(Path("~/dotfiles"))
        "git"

    """
    current = (start_path or Path.cwd()).resolve()

    # Walk up directory tree
    while current != current.parent:
        if (current / ".jj").exists():
            logger.debug(f"Found jujutsu repo at {current}")
            return "jj"
        if (current / ".git").exists():
            logger.debug(f"Found git repo at {current}")
            return "git"
        current = current.parent

    logger.debug("No VCS directory found")
    return None


@lru_cache(maxsize=1)
def get_vcs_type_cached(start_path: str = ".") -> VCSType:
    """Get VCS type with session-level caching.

    This is the PRIMARY method you should use. It:
    1. Checks filesystem first (fast)
    2. Falls back to "git" as default
    3. Caches result for the session

    Args:
        start_path: Starting directory (default: current directory)

    Returns:
        VCS type ("git" or "jj")

    Note:
        - Cached per Python session (cleared on restart)
        - Safe to call repeatedly - first call does the work
        - Default is "git" if no VCS found (most common)

    Example:
        >>> vcs = get_vcs_type_cached()
        >>> print(vcs)
        "git"

    """
    path = Path(start_path)
    detected = detect_vcs_from_filesystem(path)

    if detected:
        logger.info(f"VCS type detected: {detected}")
        return detected

    # Default to git if no VCS found
    logger.warning("No VCS detected, defaulting to git")
    return "git"


# --- VCS Detection (Slow Path: Memory) ---


async def detect_vcs_from_memory() -> VCSType | None:
    """Detect VCS type from memory (fallback method).

    This is the SLOW PATH - queries the vector database for system metadata.
    Use this only when:
    - Not in a dotfiles directory
    - Need to know user's preferred VCS across machines
    - Filesystem detection failed

    Returns:
        VCS type from memory or None if not found

    Performance:
        - Typical: 10-50ms (memory query + embedding)
        - Much slower than filesystem check

    Example:
        >>> vcs = await detect_vcs_from_memory()
        >>> print(vcs)
        "jj"  # User's preferred VCS from system baseline

    """
    try:
        from ..config import ServerConfig
        from ..core.memory import MemoryManager

        # Initialize config
        config = ServerConfig()
        # Initialize memory_manager
        memory_manager = MemoryManager(config=config)

        # Search for system baseline metadata
        result = await memory_manager.search("version_control", limit=1)

        if not result.get("results"):
            logger.debug("No VCS info in memory")
            return None

        memory_text = result["results"][0].get("memory", "")

        # Parse VCS from memory text
        if (
            "version_control: 'jj'" in memory_text
            or 'version_control: "jj"' in memory_text
        ):
            logger.info("Found VCS in memory: jj")
            return "jj"
        elif (
            "version_control: 'git'" in memory_text
            or 'version_control: "git"' in memory_text
        ):
            logger.info("Found VCS in memory: git")
            return "git"

        logger.debug("VCS info in memory but couldn't parse")
        return None

    except Exception as e:
        logger.error(f"Error querying memory for VCS: {e}")
        return None


async def detect_vcs_type(start_path: Path | None = None) -> VCSType:
    """Detect VCS type using hybrid approach.

    Strategy:
    1. Check filesystem first (fast, 1-5ms)
    2. If not found, check memory (slow, 10-50ms)
    3. Default to "git" if neither works

    This is the RECOMMENDED method for tools that need VCS detection.

    Args:
        start_path: Directory to check (default: current working directory)

    Returns:
        VCS type, guaranteed to return a value (defaults to "git")

    Example:
        >>> vcs = await detect_vcs_type()
        >>> print(vcs)
        "git"

    """
    actual_path = start_path or Path.cwd()
    # Fast path: filesystem
    filesystem_vcs = detect_vcs_from_filesystem(actual_path)
    if filesystem_vcs:
        return filesystem_vcs

    # Slow path: memory
    logger.debug("Filesystem check failed, trying memory")
    memory_vcs = await detect_vcs_from_memory()
    if memory_vcs:
        return memory_vcs

    # Default
    logger.warning("No VCS detected anywhere, defaulting to git")
    return "git"


# --- VCS Command Execution ---


class VCSCommand:
    """Helper for executing VCS commands safely."""

    def __init__(self, vcs_type: VCSType, cwd: Path | None = None):
        """Initialize the VCS helper with a type and working directory."""
        self.vcs_type: VCSType = vcs_type
        self.cwd: Path | None = cwd

    def run(self, args: list[str], timeout: int = 10, cwd: Path | None = None) -> str:
        """Execute a VCS command with error handling.

        Args:
            args: Command arguments (e.g., ["status", "--short"])
            timeout: Max seconds to wait (default: 10)
            cwd: Working directory (default: self.cwd or current)

        Returns:
            Command output as string

        Raises:
            subprocess.CalledProcessError: If command fails
            subprocess.TimeoutExpired: If command times out

        Example:
            >>> vcs = VCSCommand("git")
            >>> output = vcs.run(["status", "--short"])
            >>> print(output)
            "M .zshrc"

        """
        cmd = [self.vcs_type] + args
        actual_cwd = cwd or self.cwd

        logger.debug(f"Running VCS command: {' '.join(cmd)} (cwd: {actual_cwd})")

        try:
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                cwd=actual_cwd,
                text=True,
            )
            return output

        except subprocess.CalledProcessError as e:
            logger.error(f"VCS command failed: {e.output}")  # pyright: ignore[reportAny]
            raise

        except subprocess.TimeoutExpired:
            logger.error(f"VCS command timed out after {timeout}s")
            raise

    def get_status(self, timeout: int | None = None) -> str:
        """Get repository status (uncommitted changes)."""
        args = ["st", "--no-pager"] if self.vcs_type == "jj" else ["status", "--short"]
        return self.run(args, timeout=timeout) if timeout else self.run(args)

    def get_log(self, count: int = 20, timeout: int | None = None) -> str:
        """Get commit history."""
        if self.vcs_type == "jj":
            args = ["log", "all", "--no-pager", "-n", str(count)]
        else:
            args = [
                "--no-pager",
                "log",
                "--graph",
                "--oneline",
                "--all",
                "--decorate",
                "-n",
                str(count),
            ]
        return self.run(args, timeout=timeout) if timeout else self.run(args)

    def get_current_commit(self, timeout: int | None = None) -> str:
        """Get current commit hash."""
        if self.vcs_type == "jj":
            args = ["log", "-r", "@", "--no-graph", "-T", "commit_id"]
        else:
            args = ["rev-parse", "HEAD"]

        res = self.run(args, timeout=timeout) if timeout else self.run(args)
        return res.strip()


# --- High-Level Helper Functions ---


async def get_vcs_command(start_path: Path | None = None) -> VCSCommand:
    """Get a VCSCommand instance for the detected VCS type.

    This is a convenience function that combines detection + command execution.

    Args:
        start_path: Directory to check for VCS

    Returns:
        VCSCommand instance ready to execute commands

    Example:
        >>> vcs = await get_vcs_command()
        >>> status = vcs.get_status()
        >>> print(status)
        "M .zshrc"

    """
    actual_path = start_path or Path.cwd()
    vcs_type = await detect_vcs_type(actual_path)
    return VCSCommand(vcs_type, cwd=actual_path)


def is_in_repo(path: Path | None = None) -> bool:
    """Check if path is inside a git or jj repository.

    Args:
        path: Path to check (default: current directory)

    Returns:
        True if inside a repo, False otherwise

    Example:
        >>> is_in_repo(Path("~/dotfiles"))
        True
        >>> is_in_repo(Path("/tmp"))
        False

    """
    actual_path = path or Path.cwd()
    return detect_vcs_from_filesystem(actual_path) is not None


def get_repo_root(path: Path | None = None) -> Path | None:
    """Find the root directory of the repository.

    Args:
        path: Starting path (default: current directory)

    Returns:
        Path to repo root or None if not in a repo

    Example:
        >>> get_repo_root(Path("~/dotfiles/zsh"))
        Path("~/dotfiles")

    """
    current = (path or Path.cwd()).resolve()

    while current != current.parent:
        if (current / ".jj").exists() or (current / ".git").exists():
            return current
        current = current.parent

    return None


# --- Validation Helpers ---


def validate_vcs_installed(vcs_type: VCSType) -> bool:
    """Check if VCS binary is installed and accessible.

    Args:
        vcs_type: "git" or "jj"

    Returns:
        True if installed, False otherwise

    Example:
        >>> validate_vcs_installed("git")
        True
        >>> validate_vcs_installed("jj")
        False  # If jujutsu not installed

    """
    try:
        subprocess.run(
            [vcs_type, "--version"], check=True, capture_output=True, timeout=2
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return False
