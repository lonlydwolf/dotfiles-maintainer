"""Troubleshooting and knowledge base tools.

This module provides tools to record solutions to configuration errors and
search the accumulated knowledge base to prevent re-solving the same issues.
"""

import logging

from ..core.memory import MemoryManager
from ..core.types import MemoryResult

logger = logging.getLogger(__name__)


async def log_troubleshooting_event(
    memory: MemoryManager, error_signature: str, root_cause: str, fix_steps: str
) -> str:
    """Record a bug fix in the semantic knowledge base.

    Call this AFTER successfully fixing a configuration issue. It builds a
    long-term memory of errors, their causes, and the verified solutions.

    Args:
        memory: The core memory manager instance.
        error_signature: Unique pattern or message identifying the error.
        root_cause: The strategic reason behind the failure.
        fix_steps: Detailed, reproducible steps taken to resolve the issue.

    Returns:
        A confirmation message stating the knowledge base was updated.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata
          `type: troubleshoot`.

    """
    try:
        troubleshoot_text = f"""Troubleshooting: {error_signature}
        Cause: {root_cause}
        Fix: {fix_steps}
        """
        response = await memory.add_with_redaction(
            troubleshoot_text,
            metadata={"type": "troubleshoot", "error": error_signature},
        )

        if not response.results:
            duplicate_detected = f"""⚠️ Troubleshooting Knowledge Base not updated (duplicate detected)

            Troubleshooting: {error_signature}
            Cause: {root_cause}
            Fix: {fix_steps}
            Note: A similar Knowledge was already recorded."""

            logger.warning(f"Troubleshooting duplicate detected for '{error_signature}'.")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Troubleshooting Knowledge logged to memory

        Memory ID: {event.id}
        Event: {event.event}
        Troubleshooting: {error_signature}
        Cause: {root_cause}
        Fix: {fix_steps}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Troubleshooting knowledge logged for '{error_signature}' (ID: {event.id})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_msg = f"Failed to add {error_signature} troubleshooting to memory: {e}"
        logger.error(err_msg)
        return err_msg


async def get_troubleshooting_guide(
    memory: MemoryManager, error_keyword: str
) -> list[MemoryResult]:
    """Search for past solutions to configuration errors.

    Call this FIRST when an error occurs. It searches the knowledge base for
    similar past signatures to see if a verified fix already exists.

    Args:
        memory: The core memory manager instance.
        error_keyword: Keywords from the current error to search for.

    Returns:
        A list of MemoryResult objects containing past solutions.

    """
    try:
        search_results = await memory.search(f"troubleshooting {error_keyword}")
        logger.debug(
            f"Retrieved {len(search_results.results)} troubleshooting logs for '{error_keyword}'"
        )
        return search_results.results

    except Exception as e:
        logger.error(
            f"Failed to retrieve logs for troubleshooting '{error_keyword}': {e}"
        )
        return []
