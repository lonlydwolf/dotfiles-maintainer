"""Configuration lifecycle tracking tools.

This module provides tools to track long-term changes like tool migration,
deprecation, and permanent removal of configurations.
"""

import logging
from datetime import datetime, timezone
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
        lifecycle_text = f"""
        Lifecycle Event: {action}
        Target Config: {old_config.app_name}
        Replaced by: {new_config.app_name if new_config else "None"}
        Logic: {logic}
        Timestamp: {datetime.now(timezone.utc).isoformat()}
        """.strip()

        response = await memory.add_with_redaction(
            lifecycle_text,
            metadata={
                "type": "lifecycle",
                "event": action,
                "app": old_config.app_name,
                "replacement": new_config.app_name if new_config else "None",
                "logic": logic,
            },
        )

        if not response.results:
            duplicate_detected = f"""⚠️ Lifecycle not logged (duplicate detected)

            Lifecycle Event: {action}
            Target Config: {old_config.app_name}
            Replaced by: {new_config.app_name if new_config else "None"}
            Logic: {logic}
            Timestamp: {datetime.now(timezone.utc).isoformat()}
            Note: A similar lifecycle was already recorded."""
            logger.warning(f"Lifecycle event {action} for {old_config.app_name} duplicate detected.")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Lifecycle event logged to memory

        Memory ID: {event.id}
        Event: {event.event}
        Lifecycle Event: {action}
        Target Config: {old_config.app_name}
        Replaced by: {new_config.app_name if new_config else "None"}
        Logic: {logic}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Lifecycle event logged to memory (ID: {event.id}, Action: {action})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_msg = f"Failed to log Lifecycle Event: {e}"
        logger.error(err_msg)
        return err_msg
