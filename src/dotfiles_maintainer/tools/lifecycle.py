"""Configuration lifecycle tracking tools.

This module provides tools to track long-term changes like tool migration,
deprecation, and permanent removal of configurations.
"""

import logging
from typing import Literal

from ..core.memory import MemoryManager
from ..core.types import AppConfig

logger = logging.getLogger(__name__)


async def track_lifecycle_events(
    memory: MemoryManager,
    action: Literal["DEPRECATE", "REPLACE"],
    old_config: AppConfig,
    new_config: AppConfig | None,
    logic: str,
) -> str:
    """Record tool migration, deprecation, or permanent removal.

    Use this when switching between tools (e.g., Bash to Zsh, or Vim to
    Neovim) or removing a tool's configuration entirely. It ensures the
    agent doesn't accidentally suggest deprecated tools in the future.

    Workflow:
    1. Agent identifies a replacement or deprecation event.
    2. Agent asks user for the migration reasoning.
    3. Agent calls this tool to log the event in semantic memory.

    Args:
        memory: The core memory manager instance.
        action: The lifecycle event type ('DEPRECATE' or 'REPLACE').
        old_config: The current/outgoing application configuration.
        new_config: The incoming configuration (required if action is 'REPLACE').
        logic: The strategic reasoning behind the transition.

    Returns:
        A confirmation message stating the lifecycle event has been logged.

    Raises:
        Exception: Captures errors during memory storage.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata `type: lifecycle`.

    Example:
        >>> result = await track_lifecycle_events(memory, "REPLACE", old_vim, new_nvim, "Better LSP")
        >>> print(result)
        "Lifecycle Event: REPLACE on Vim... logged in memory"

    """
    try:
        msg = f"Lifecycle Event: {action} on {old_config['app_name']}. "
        if new_config:
            msg += f"Replaced by {new_config['app_name']}. "
        msg += f"Logic: {logic}"

        await memory.add_with_redaction(msg, metadata={"type": "lifecycle"})

        output = f"{msg} has been logged in memory"
        logger.info(output)
        return output

    except Exception as e:
        err_msg = f"Failed to log Lifecycle Event: {e}"
        logger.error(err_msg)
        return err_msg
