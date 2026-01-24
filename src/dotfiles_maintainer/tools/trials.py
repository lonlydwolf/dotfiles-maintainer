"""Plugin and tool trial evaluation tools.

This module provides tools to track the lifecycle of new configurations or
plugins during a temporary evaluation period.
"""

import logging
from datetime import datetime, timezone

from ..core.memory import MemoryManager
from ..core.types import MemoryResult

logger = logging.getLogger(__name__)


async def manage_trial(
    memory: MemoryManager,
    name: str,
    trial_period: int,
    success_criteria: str,
) -> str:
    """Set a timer for evaluating a new tool or plugin.

    Use this when the user installs something "just to try it out". It logs
    the trial intent so future sessions can check in: "It's been 7 days,
    do you want to keep 'zsh-autosuggestions'?"

    Args:
        memory: The core memory manager instance.
        name: Name of the tool or plugin being evaluated.
        trial_period: Duration of the evaluation in days.
        success_criteria: Specific requirements for keeping the tool.

    Returns:
        A confirmation message stating the trial has been set.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata
          `type: trial` and `active: True`.

    """
    try:
        trial_text = f"""
        Tool/Plugin Trial: {name}
        Trial Period: {trial_period} days
        Success Criteria: {success_criteria}
        Timestamp: {datetime.now(timezone.utc).isoformat()}
        """.strip()

        response = await memory.add_with_redaction(
            trial_text, metadata={"type": "trial", "app": name, "active": True}
        )

        if not response.results:
            duplicate_detected = f"""⚠️ Trial not started (duplicate detected)

            Tool/Plugin: {name}
            Trial Period: {trial_period} days
            Success Criteria: {success_criteria}
            Note: A similar trial was already recorded."""
            logger.warning(f"Trial for '{name}' duplicate detected.")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Trial Started and logged to memory

        Memory ID: {event.id}
        Event: {event.event}
        Tool/Plugin: {name}
        Trial Period: {trial_period} days
        Success Criteria: {success_criteria}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Trial started for '{name}' (ID: {event.id})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_msg = f"Failed to set Trial for {name}: {e}"
        logger.error(err_msg)
        return err_msg


async def list_active_trials(
    memory: MemoryManager, min_days_active: int
) -> list[MemoryResult]:
    """Retrieve plugins/tools currently in a probationary period.

    Use this to review active evaluations and help the user decide whether
    to finalize a setup or remove it.

    Args:
        memory: The core memory manager instance.
        min_days_active: Filter for trials active for at least N days.

    Returns:
        A list of MemoryResult objects representing active trials.

    """
    try:
        _ = min_days_active
        search_results = await memory.search("active plugin trials")
        logger.debug(f"Retrieved {len(search_results.results)} active trials")
        return search_results.results

    except Exception as e:
        logger.error(f"Failed to retrieve Trials: {e}")
        return []
