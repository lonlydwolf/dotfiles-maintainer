"""Configuration change tracking tools.

This module provides tools to record configuration changes with semantic
context, capturing the rationale behind modifications.
"""

import logging

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
        msg = f"{data['app_name']} change({data['change_type']}) -> {data['description']} \n Why? {data['rationale']} \n Improvement: {data['improvement_metric']} "

        if data.get("vcs_commit_id"):
            msg += f"\nVCS Commit: {data['vcs_commit_id']}"

        result = await memory.add_with_redaction(msg, metadata={"type": "change"})

        return f"Success: {result}"

    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return f"Error: {str(e)}"
