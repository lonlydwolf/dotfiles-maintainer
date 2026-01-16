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
        msg = (
            f"Troubleshooting: {error_signature}\nCause: {root_cause}\nFix: {fix_steps}"
        )
        await memory.add_with_redaction(msg, metadata={"type": "troubleshoot"})
        output = f"Troubleshooting Knowledge Base Updated. Added: {error_signature}"
        logger.info(output)
        return output
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
        raw_results = await memory.search(f"troubleshooting {error_keyword}")
        result = raw_results.get("results", [])
        logger.info(
            f"Retrieved {len(result)} troubleshooting logs for '{error_keyword}'"
        )
        return result

    except Exception as e:
        logger.error(
            f"Failed to retrieve logs for troubleshooting '{error_keyword}': {e}"
        )
        return []
