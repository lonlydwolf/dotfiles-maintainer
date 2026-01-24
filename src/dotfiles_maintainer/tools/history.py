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
        memory_msg = f"""Historical Context({vcs}):
        {output}
        """.strip()
        response = await memory.add_with_redaction(
            memory_msg, metadata={"type": "history", "vcs": vcs, "count": str(count)}
        )

        if not response.results:
            duplicate_detected = f"""⚠️ Historical Context not ingested

            VCS: {vcs}
            Reason: No new facts were extracted by the memory engine, or the history is identical to existing memories.
            """.strip()

            logger.warning("Historical Context not ingested (No new facts or duplicate).")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Ingested last {count} ({vcs}) commits to memory

        Memory ID: {event.id}
        Event: {event.event}
        Historical Context:
        ```
        {output}
        ```

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Ingested last {count} {vcs} commits to memory (ID: {event.id})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_msg: str = f"Error ingesting history: {e}"
        logger.error(err_msg)
        return err_msg
