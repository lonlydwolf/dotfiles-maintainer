"""Configuration context and dependency query tools.

This module provides tools to retrieve historical context, search change
history, and verify system dependencies from semantic memory.
"""

import logging

from ..core.memory import MemoryManager
from ..core.types import AppConfig, MemoryResult

logger = logging.getLogger(__name__)


async def get_config_context(
    memory: MemoryManager, app_name: str
) -> list[MemoryResult]:
    """Retrieve historical context and preferences for a tool.

    Call this BEFORE suggesting any changes to a specific application. It
    fetches all relevant memories, past changes, and user constraints from
    semantic memory to ensure new suggestions are consistent with the past.

    Args:
        memory: The core memory manager instance.
        app_name: The name of the application to query (e.g., 'zsh', 'nvim').

    Returns:
        A list of MemoryResult objects containing past rationales and settings.

    Side Effects:
        - Persistent Memory: Performs a semantic search in the vector database.

    """
    try:
        search_results = await memory.search(app_name)
        logger.info(
            f"Retrieved {len(search_results.results)} context results for '{app_name}'"
        )
        return search_results.results

    except Exception as e:
        logger.error(f"Failed to query '{app_name}': {e}")
        return []


async def search_change_history(
    memory: MemoryManager, query: str, app_name: str | None = None
) -> list[MemoryResult]:
    """Search for specific past decisions or change events.

    Use this when you need to answer specific 'Why' or 'When' questions,
    such as 'Why did we disable the git prompt?' or 'When did we switch
    to Alacritty?'.

    Args:
        memory: The core memory manager instance.
        query: The semantic search query (e.g., 'font size', 'latency').
        app_name: Optional application name to narrow the search scope.

    Returns:
        A list of matching MemoryResult objects.

    """
    search_query = query
    if app_name:
        search_query = f"{app_name}: {query}"

    try:
        search_results = await memory.search(search_query)
        logger.info(
            f"Retrieved {len(search_results.results)} history results for '{search_query}'"
        )
        return search_results.results

    except Exception as e:
        logger.error(f"Failed to query '{search_query}': {e}")
        return []


async def check_system_dependencies(
    memory: MemoryManager, tool_name: str
) -> list[MemoryResult]:
    """Check for known dependencies or conflicts recorded in memory.

    Call this before installing or configuring a tool to ensure all
    prerequisites are met and avoid repeating past compatibility mistakes.

    Args:
        memory: The core memory manager instance.
        tool_name: The name of the tool or plugin to check.

    Returns:
        A list of matching records detailing dependencies or conflicts.

    """
    try:
        search_results = await memory.search(tool_name)
        logger.info(
            f"Retrieved {len(search_results.results)} dependency results for '{tool_name}'"
        )
        return search_results.results

    except Exception as e:
        logger.error(f"Failed to query '{tool_name}': {e}")
        return []


async def sync_work_in_progress(
    memory: MemoryManager,
    session_goal: str,
    modified_files: list[AppConfig],
    current_struggle: str,
) -> str:
    """Save session state when a task is not yet complete.

    Call this at the end of a session to store the 'mental state' (what was
    tried, what failed, and the current goal). This allows a future agent
    session to pick up exactly where you left off.

    Args:
        memory: The core memory manager instance.
        session_goal: The primary objective of the current session.
        modified_files: Configurations touched during the session.
        current_struggle: Details on blockers or errors preventing completion.

    Returns:
        A confirmation message stating the WIP has been synchronized.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata `type: wip`.

    """
    try:
        files = [f.app_name for f in modified_files]
        msg = f"WIP Session Goal: {session_goal}\nModified: {files}\nStruggle: {current_struggle}"
        await memory.add_with_redaction(msg, metadata={"type": "wip"})
        logger.info("WIP synchronized")
        return "WIP synchronized"

    except Exception as e:
        err_msg = f"Failed synchronize WIP: {e}"
        logger.error(err_msg)
        return err_msg
