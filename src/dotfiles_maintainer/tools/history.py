"""VCS history ingestion tools.

This module provides tools to backfill semantic memory using existing commit
logs from version control systems.
"""

import logging

from ..core.memory import MemoryManager
from ..utils.vcs import VCSCommand, detect_vcs_type

logger = logging.getLogger(__name__)


async def ingest_version_history(
    memory: MemoryManager, count: int = 20, timeout: int = 10
) -> str:
    """Backfill semantic memory with project's recent history.

    Use this when first connecting to an existing dotfiles repository. It
    reads commit logs and adds them to memory, giving the agent context on
    past decisions made before it arrived.

    Workflow:
    1. Detects VCS type (git/jj).
    2. Retrieves the last N commit logs from version control.
    3. Stores the combined history in semantic memory with 'history' metadata.

    Args:
        memory: The core memory manager instance.
        count: Number of past commits to ingest (default: 20).
        timeout: VCS command timeout in seconds (default: 10).

    Returns:
        A confirmation message summarizing the number of commits ingested
        and the VCS type used.

    Raises:
        Exception: Captures errors during VCS command execution or memory addition.

    Side Effects:
        - Persistent Memory: Adds a substantial new memory entry with
          metadata `type: history`.
        - Subprocess: Executes `git log` or `jj log`.

    Example:
        >>> result = await ingest_version_history(memory, count=10)
        >>> print(result)
        "Ingested last 10 git commit into memory."

    """
    try:
        vcs = await detect_vcs_type()
        vcs_command = VCSCommand(vcs)
        output = vcs_command.get_log(count=count, timeout=timeout)
        await memory.add_with_redaction(
            f"Historical Context ({vcs}):\n{output}", metadata={"type": "history"}
        )
        result = f"Ingested last {count} {vcs} commit into memory."
        logger.info(result)
        return result

    except Exception as e:
        err_msg: str = f"Error ingesting history: {e}"
        logger.error(err_msg)
        return err_msg
