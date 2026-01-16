"""System baseline initialization tools.

This module establishes the ground truth for a user's system environment.
"""

import logging

from ..core.memory import MemoryManager
from ..core.types import AppConfig, SystemMetadata

logger = logging.getLogger(__name__)


async def initialize_system_baseline(
    memory_manager: MemoryManager,
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
        data = f"User System -> dotfile_manager: {manager_name}\nconfigs: {config_map}\nsystem_metadata: {system_metadata}"
        await memory_manager.add_with_redaction(data, metadata={"type": "baseline"})

        logger.info(f"System Baseline Initialized:\n{data}")
        return f"System Baseline Initialized:\n{data}"

    except Exception as e:
        err_out: str = f"Failed to Initialize Baseline: {e}"
        logger.error(err_out)
        return err_out
