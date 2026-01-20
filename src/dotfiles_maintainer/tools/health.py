"""Server health and diagnostics tools.

This module provides tools to verify the operational status of the server
components, including memory database connectivity and VCS availability.
"""

import logging

from ..config import ServerConfig
from ..core.memory import MemoryManager
from ..core.types import HealthStatus
from ..utils.vcs import detect_vcs_type

logger = logging.getLogger(__name__)


async def health_check(
    config: ServerConfig, memory_manager: MemoryManager
) -> HealthStatus:
    """Verify all server components are operational.

    This tool performs a diagnostic check on the primary subsystems to ensure
    the environment is ready for dotfiles management.

    Workflow:
    1. Memory: Performs a search ping to verify Qdrant connectivity.
    2. VCS: Detects current version control type to ensure binaries are in PATH.
    3. LLM: Checks if an API key is configured for the selected provider.

    Args:
        config: The current server configuration.
        memory_manager: The active memory manager instance.

    Returns:
        A HealthStatus dictionary containing:
            - status: Overall health state ('healthy' or 'unhealthy').
            - version: Current server version.
            - components: Detailed status for 'memory', 'vcs', and 'llm_provider'.

    Raises:
        Exception: Captures diagnostic errors, returning 'unhealthy' with details.

    Side Effects:
        - Network/Database: Performs a lightweight search query to the vector database.
        - Subprocess: May execute VCS binaries for version checks.

    Example:
        >>> status = await health_check(config, memory)
        >>> print(status["status"])
        "healthy"

    """
    components: dict[str, str] = {}

    # 1. Check Memory (Qdrant)
    try:
        # Simple ping by searching for something unlikely to exist, just to check connection
        await memory_manager.search("health_check_ping", limit=1)
        components["memory"] = "connected"
    except Exception as e:
        logger.error(f"Health check failed for memory: {e}")
        components["memory"] = f"error: {str(e)}"

    # 2. Check VCS
    try:
        vcs = await detect_vcs_type()
        components["vcs"] = f"active ({vcs})"
    except Exception as e:
        logger.error(f"Health check failed for VCS: {e}")
        components["vcs"] = f"error: {str(e)}"

    # 3. Check LLM
    if config.llm_key:
        components["llm_provider"] = f"configured ({config.llm_provider})"
    else:
        components["llm_provider"] = "missing_key"

    # Determine overall status
    overall_status = "healthy"
    for status in components.values():
        if "error" in status or "missing" in status:
            overall_status = "unhealthy"
            break

    return HealthStatus(
        status=overall_status,
        version="1.0.0",  # This could be dynamically loaded from pyproject.toml if needed
        components=components,
    )
