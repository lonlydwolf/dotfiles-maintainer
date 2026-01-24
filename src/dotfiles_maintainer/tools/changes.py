"""Configuration change tracking tools.

This module provides tools to record configuration changes with semantic
context, capturing the rationale behind modifications.
"""

import logging
from datetime import datetime, timezone

from ..core.memory import MemoryManager
from ..core.types import AppChange

logger = logging.getLogger(__name__)


async def commit_contextual_change(
    memory: MemoryManager,
    data: AppChange,
) -> str:
    """Record configuration change with semantic context (WHY and WHAT).

    Call this IMMEDIATELY after making ANY changes to a configuration file.
    It logs the rationale and description, creating a semantic history that
    is far more useful for future reasoning than a simple VCS commit.

    Workflow:
    1. User requests a change to a configuration.
    2. Agent performs the modification on the filesystem.
    3. Agent confirms with User that the change is complete.
    4. Agent calls this tool to commit the change context to semantic memory.
    5. Agent informs user that the change and its rationale have been remembered.

    Args:
        memory: The core memory manager instance.
        data: A dictionary containing details about the change:
            - app_name: The tool being modified (e.g., 'zsh', 'nvim').
            - change_type: Category (e.g., 'optimization', 'fix', 'keybind').
            - description: Detailed explanation of WHAT changed.
            - rationale: The strategic reason for WHY the change was made.
            - improvement_metric: Quantifiable benefit (e.g., 'startup -50ms').
            - vcs_commit_id: Optional git/jj commit hash for cross-referencing.

    Returns:
        A confirmation message indicating the change was successfully logged
        or an error message.

    Raises:
        Exception: Captures and logs errors during memory storage.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata `type: change`.

    Example:
        >>> result = await commit_contextual_change(memory, change_data)
        >>> print(result)
        "Success: Memory added with ID ..."

    """
    try:
        change_text = f"""
        Configuration Change: {data.app_name}
        Type: {data.change_type}
        Rationale: {data.rationale}
        Improvement: {data.improvement_metric}
        Description: {data.description}
        VCS Commit: {data.vcs_commit_id}
        Timestamp: {datetime.now(timezone.utc).isoformat()}
        """.strip()

        response = await memory.add_with_redaction(
            change_text,
            metadata={
                "type": "change",
                "app": data.app_name,
                "change_type": data.change_type,
                "vcs_commit": data.vcs_commit_id,
            },
        )

        if not response.results:
            duplicate_detected = f"""⚠️ Change not logged (duplicate detected)

            App: {data.app_name}
            Type: {data.change_type}
            Note: A similar change was already recorded."""
            logger.warning(f"Change for {data.app_name} duplicate detected. No new memory added.")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Change logged to memory

        Memory ID: {event.id}
        Event: {event.event}
        App: {data.app_name}
        Type: {data.change_type}
        Impact: {data.improvement_metric}
        Rationale: {data.rationale[:100]}{"..." if len(data.rationale) > 100 else ""}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Change logged to memory (ID: {event.id}, App: {data.app_name})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_msg = f"Failed to log change to memory: {e}"
        logger.error(err_msg)
        return err_msg
