"""Memory correction and update tools.

This module provides tools to edit existing semantic memories when they are
found to be incorrect or outdated.
"""

import logging

from ..core.memory import MemoryManager

logger = logging.getLogger(__name__)


async def update_memory(memory: MemoryManager, memory_id: str, new_text: str) -> str:
    """Edit or correct an existing semantic memory entry.

    Use this when you realize a stored memory contains incorrect information
    or is no longer relevant (e.g., "Actually, we use Kitty, not Alacritty").

    Workflow:
    1. Agent identifies a flawed memory via search or context retrieval.
    2. Agent extracts the `memory_id` (UUID) from the search results.
    3. Agent calls this tool with the ID and corrected text.

    Args:
        memory: The core memory manager instance.
        memory_id: The unique identifier (UUID) of the memory to edit.
        new_text: The complete, corrected content of the memory.

    Returns:
        A confirmation message stating the update was successful.

    Side Effects:
        - Persistent Memory: Modifies an existing entry in the vector database.

    """
    try:
        await memory.update(memory_id, new_text)
        output = f"Memory {memory_id} updated successfully."
        logger.info(output)
        return output

    except Exception as e:
        err_msg = f"Error updating memory[{memory_id}]: {e}"
        logger.error(err_msg)
        return err_msg
