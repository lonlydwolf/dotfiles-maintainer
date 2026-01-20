"""Future planning and roadmap tracking tools.

This module provides tools to store and retrieve long-term goals, ideas, and
potential improvements for the configuration ecosystem.
"""

import logging
from typing import Literal

from ..core.memory import MemoryManager
from ..core.types import MemoryResult

logger = logging.getLogger(__name__)


async def log_conceptual_roadmap(
    memory: MemoryManager,
    idea_title: str,
    hypothesis: str,
    blockers: str,
    priority: Literal["LOW", "MEDIUM", "HIGH"],
) -> str:
    """Store future ideas or "Nice to Have" features for later consideration.

    Use this when a user mentions a goal or a new tool they aren't ready to
    implement yet (e.g., "User wants to try Hyprland but needs a better GPU").

    Args:
        memory: The core memory manager instance.
        idea_title: Strategic name for the idea or tool.
        hypothesis: Proposed implementation details and expected benefits.
        blockers: Known issues or requirements preventing immediate action.
        priority: The relative importance of this idea.

    Returns:
        A confirmation message stating the roadmap entry was saved.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata `type: roadmap`.

    """
    try:
        msg = f"Roadmap Idea: {idea_title}\nHypothesis: {hypothesis}\nBlockers: {blockers}\nPriority: {priority}"

        await memory.add_with_redaction(
            msg, metadata={"type": "roadmap", "priority": priority}
        )

        output = "Roadmap Entry saved"
        logger.info(output)
        return output

    except Exception as e:
        err_msg = f"Failed to save Roadmap Entry: {e}"
        logger.error(err_msg)
        return err_msg


async def query_roadmap(
    memory: MemoryManager,
    status: Literal["pending", "blocked"],
    priority: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
) -> list[MemoryResult]:
    """Retrieve planned features or blocked ideas from the roadmap.

    Call this when the user asks "What should we work on next?" to see past
    conceptual goals and their current priority/blockers.

    Args:
        memory: The core memory manager instance.
        status: Filter by 'pending' (ready) or 'blocked' status.
        priority: Optional filter for specific priority levels.

    Returns:
        A list of MemoryResult objects representing roadmap items.

    """
    try:
        query = f"roadmap {status}"
        if priority:
            query += f" {priority} priority"

        search_results = await memory.search(query)

        logger.info(
            f"Retrieved {len(search_results.results)} roadmap items for query '{query}'"
        )
        return search_results.results

    except Exception as e:
        logger.error(f"Failed to retrieve future ideas: {e}")
        return []
