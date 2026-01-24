"""Configuration drift detection tools.

This module provides tools to verify if the local filesystem configuration
matches the state recorded in version control.
"""

import logging

from ..core.memory import MemoryManager
from ..core.types import DriftResult
from ..utils.vcs import get_vcs_command

logger = logging.getLogger(__name__)


async def check_config_drift(memory: MemoryManager, timeout: int = 10) -> DriftResult:
    """Detect configuration drift by comparing filesystem to VCS.

    Call this at the START of every session to detect uncommitted or
    unauthorized changes. It ensures the agent's mental model remains
    synced with the actual filesystem state.

    Workflow:
    1. Detects VCS type (git/jj) from filesystem or memory.
    2. Executes the appropriate status command (e.g., `git status` or `jj st`).
    3. If changes are found, it logs them to memory with 'drift' metadata.
    4. Returns a structured report to the agent.

    Args:
        memory: The core memory manager instance.
        timeout: VCS command timeout in seconds (default: 10).

    Returns:
        A DriftResult dictionary containing:
            - status: 'clean' (no drift), 'modified' (drift found), or 'error'.
            - vcs_type: 'git' or 'jj'.
            - modified_files: List of paths that have uncommitted changes.
            - total_changes: Count of modified files.
            - message: Human-readable summary of the drift status.

    Raises:
        Exception: Captures errors during VCS command execution or memory logging.

    Side Effects:
        - Persistent Memory: If drift is detected, adds a memory entry with
          metadata `type: drift`.
        - Subprocess: Executes shell commands for version control status.

    Note:
        If drift is detected, the agent should present these changes to the
        user and ask whether to ingest them (via commit_contextual_change)
        or revert them.

    """
    try:
        vcs_cmd = await get_vcs_command()
        vcs_type = vcs_cmd.vcs_type
        output = vcs_cmd.get_status(timeout=timeout)

        if not output.strip():
            return DriftResult(
                status="clean",
                vcs_type=vcs_type,
                modified_files=[],
                total_changes=0,
                message="No drift detected. System matches repository state.",
            )

        modified_files = [line.strip() for line in output.splitlines() if line.strip()]

        drift_text = f"""Drift detected
        VCS: {vcs_type}
        Level: {output}
        """.strip()

        response = await memory.add_with_redaction(
            drift_text,
            metadata={
                "type": "drift",
                "vcs": vcs_type,
            },
        )

        # Primary event
        event = response.results[0]

        memory_log = f"""✓ Drift detected and saved to memory

        Memory ID: {event.id}
        Event: {event.event}
        VCS: {vcs_type}
        Level: {output}

        {f"Note: {len(response.results)} memories affected" if len(response.results) > 1 else ""}""".strip()

        logger.info(f"Drift detected and saved to memory (ID: {event.id}, Files: {len(modified_files)})")
        logger.debug(memory_log)

        return DriftResult(
            status="modified",
            vcs_type=vcs_type,
            modified_files=modified_files,
            total_changes=len(modified_files),
            message=memory_log,
        )

    except Exception as e:
        logger.error(f"Error checking drift: {str(e)}")
        return DriftResult(
            status="error",
            vcs_type="git",  # Default if error before detection
            modified_files=[],
            total_changes=0,
            message=f"Error checking drift: {str(e)}",
        )
