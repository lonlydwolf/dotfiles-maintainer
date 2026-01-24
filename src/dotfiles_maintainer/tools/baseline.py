"""System baseline initialization tools.

This module establishes the ground truth for a user's system environment.
"""

import logging

from ..core.memory import MemoryManager
from ..core.types import AppConfig, SystemMetadata

logger = logging.getLogger(__name__)


async def initialize_system_baseline(
    memory: MemoryManager,
    manager_name: str,
    config_map: list[AppConfig],
    system_metadata: SystemMetadata,
) -> str:
    """Establish ground truth for the environment (OS, Shell, Hardware).

    Call this ONCE at the start of a new relationship with a user or machine.
    It records the environment details, allowing subsequent decisions to be
    hardware-aware (e.g., "Don't enable heavy blur on this Raspberry Pi").

    Workflow:
    1. Search memory for any existing initialization (Agent should do this).
    2. If not found, call this tool to start baseline initialization.
    3. The tool formats the metadata and config map into a semantic report.
    4. It stores this report in the persistent semantic memory.

    Args:
        memory_manager: The core memory manager instance.
        manager_name: Name of the dotfiles manager in use (e.g., 'stow',
            'chezmoi', 'yadm', 'rcm').
        config_map: List of all configurations on the user's system.
            Each AppConfig includes app_name, paths, structure, and dependencies.
        system_metadata: Hardware and software environment details.
            Includes OS version, main shell, terminal, editor, VCS, and CPU.

    Returns:
        A confirmation message indicating whether initialization succeeded,
        including a summary of the data stored, or an error message.

    Raises:
        Exception: Captures and logs errors during memory storage,
            returning an error string to the agent.

    Side Effects:
        - Persistent Memory: Adds a new memory entry with metadata `type: baseline`.
        - Logging: Logs the initialization event to the system logger.

    Example:
        >>> result = await initialize_system_baseline(memory, "stow", configs, metadata)
        >>> print(result)
        "System Baseline Initialized: ..."

    """
    try:
        baseline_text = f"""User System ->
        Dotfile Manager: {manager_name}
        Configs: {config_map}
        System Metadata: {system_metadata}
        """.strip()

        response = await memory.add_with_redaction(
            baseline_text,
            metadata={
                "type": "baseline",
                "dotfile_manager": manager_name,
                "configs": ", ".join([config.app_name for config in config_map]),
                "system": system_metadata.os_version,
            },
        )

        if not response.results:
            duplicate_detected = f"""⚠️ System Baseline not initialized (duplicate detected)

            Dotfile Manager: {manager_name}
            Configs: {config_map}
            System Metadata: {system_metadata}
            Note: A similar system baseline was already recorded."""

            logger.warning("System Baseline duplicate detected. No new memory added.")
            logger.debug(duplicate_detected)
            return duplicate_detected

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ System Baseline Initialized
        Memory ID: {event.id}
        Event: {event.event}
        Dotfile Manager: {manager_name}
        Configs: {config_map}
        System Metadata: {system_metadata}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"System Baseline Initialized (ID: {event.id})")
        logger.debug(memory_log)
        return memory_log

    except Exception as e:
        err_out: str = f"Failed to Initialize Baseline: {e}"
        logger.error(err_out)
        return err_out
