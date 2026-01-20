"""MCP server initialization and tool registration."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from .config import ServerConfig
from .core.memory import MemoryManager
from .core.types import (
    AppChange,
    AppConfig,
    DriftResult,
    HealthStatus,
    Mem0UpdateResponse,
    MemoryResult,
    SystemMetadata,
)
from .prompts.persona import register_persona_prompts
from .tools import (
    baseline,
    changes,
    drift,
    health,
    history,
    lifecycle,
    queries,
    roadmap,
    trials,
    troubleshooting,
    updates,
)

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    config: ServerConfig
    memory: MemoryManager


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage the application lifecycle, initializing and cleaning up resources."""
    _ = server
    config = ServerConfig()
    memory = MemoryManager(config)
    try:
        yield AppContext(config=config, memory=memory)
    finally:
        logger.info("Shutting down server and cleaning up resources...")


# Create MCP server with lifespan
mcp = FastMCP("DotfilesMaintainer", lifespan=app_lifespan)

# --- Helper to get memory from context ---


def get_memory(ctx: Context[ServerSession, AppContext]) -> MemoryManager:
    """Extract memory manager from lifespan context."""
    return ctx.request_context.lifespan_context.memory


def get_config(ctx: Context[ServerSession, AppContext]) -> ServerConfig:
    """Extract config from lifespan context."""
    return ctx.request_context.lifespan_context.config


# --- System Initialization Tools ---


@mcp.tool(
    description="Initialize system baseline. Call ONCE per machine to establish ground truth."
)
async def initialize_system_baseline(
    ctx: Context[ServerSession, AppContext],
    manager_name: str,
    config_map: list[AppConfig],
    system_metadata: SystemMetadata,
) -> str:
    """Establish ground truth for the environment (OS, Shell, Hardware)."""
    return await baseline.initialize_system_baseline(
        memory_manager=get_memory(ctx),
        manager_name=manager_name,
        config_map=config_map,
        system_metadata=system_metadata,
    )


# --- Change Tracking Tools ---


@mcp.tool(
    description="Log config change with context. Call IMMEDIATELY after modifying any dotfile."
)
async def commit_contextual_change(
    ctx: Context[ServerSession, AppContext], data: AppChange
) -> str:
    """Record configuration change with semantic context (WHY and WHAT)."""
    return await changes.commit_contextual_change(get_memory(ctx), data)


# --- Drift Detection Tools ---


@mcp.tool(description="Check for config drift. Call at session start.")
async def check_config_drift(ctx: Context[ServerSession, AppContext]) -> DriftResult:
    """Verify if local config files match the repository state."""
    return await drift.check_config_drift(
        get_memory(ctx), timeout=get_config(ctx).vcs_timeout
    )


# --- Version History Tools ---


@mcp.tool(
    description="Backfill memory with VCS history. Use when first connecting to existing repo"
)
async def ingest_version_history(
    ctx: Context[ServerSession, AppContext], count: int = 20
) -> str:
    """Read last N commits and add to memory for context."""
    return await history.ingest_version_history(
        get_memory(ctx), count, timeout=get_config(ctx).vcs_timeout
    )


# --- Lifecycle Management Tools ---


@mcp.tool(
    description="Track tool migration/removal. Use when switching/removing tools."
)
async def track_lifecycle_events(
    ctx: Context[ServerSession, AppContext],
    action: Literal["DEPRECATE", "REPLACE"],
    old_config: AppConfig,
    new_config: AppConfig | None,
    logic: str,
) -> str:
    """Log tool transitions/removal to prevent accidental suggestions of old tools."""
    return await lifecycle.track_lifecycle_events(
        get_memory(ctx), action, old_config, new_config, logic
    )


# --- Roadmap Tools ---


@mcp.tool(
    description="Store future ideas. Use for 'nice to have' features not ready to implement."
)
async def log_conceptual_roadmap(
    ctx: Context[ServerSession, AppContext],
    idea_title: str,
    hypothesis: str,
    blockers: str,
    priority: Literal["LOW", "MEDIUM", "HIGH"],
) -> str:
    """Store ideas mentioned by user but not immediately implementable."""
    return await roadmap.log_conceptual_roadmap(
        get_memory(ctx), idea_title, hypothesis, blockers, priority
    )


@mcp.tool(
    description="Retrieve roadmap items. Use when user asks 'what should we work on next?'"
)
async def query_roadmap(
    ctx: Context[ServerSession, AppContext],
    status: Literal["pending", "blocked"],
    priority: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
) -> list[MemoryResult]:
    """Retrieve planned features or blocked ideas."""
    return await roadmap.query_roadmap(get_memory(ctx), status, priority)


# --- Trial Management Tools ---


@mcp.tool(
    description="Start tool/plugin trial. Use when installing new tools for evaluation."
)
async def manage_trial(
    ctx: Context[ServerSession, AppContext],
    name: str,
    trial_period: int,
    success_criteria: str,
) -> str:
    """Set conceptual timer for tool/plugin evaluation."""
    return await trials.manage_trial(
        get_memory(ctx), name, trial_period, success_criteria
    )


@mcp.tool(
    description="List active trials. Find tools/plugins currently in probationary period."
)
async def list_active_trials(
    ctx: Context[ServerSession, AppContext], min_days_active: int
) -> list[MemoryResult]:
    """Retrieve tools/plugins being evaluated."""
    return await trials.list_active_trials(get_memory(ctx), min_days_active)


# --- Troubleshooting Tools ---


@mcp.tool(description="Log bug fix. Call AFTER fixing a bug to build knowledge base.")
async def log_troubleshooting_event(
    ctx: Context[ServerSession, AppContext],
    error_signature: str,
    root_cause: str,
    fix_steps: str,
) -> str:
    """Record solution to prevent re-solving the same issue."""
    return await troubleshooting.log_troubleshooting_event(
        get_memory(ctx), error_signature, root_cause, fix_steps
    )


@mcp.tool(description="Search troubleshooting history. Call FIRST when error occurs.")
async def get_troubleshooting_guide(
    ctx: Context[ServerSession, AppContext], error_keyword: str
) -> list[MemoryResult]:
    """Check if this error was solved before."""
    return await troubleshooting.get_troubleshooting_guide(
        get_memory(ctx), error_keyword
    )


# --- Query Tools ---


@mcp.tool(description="Get context for app. Call BEFORE suggesting changes to a tool.")
async def get_config_context(
    ctx: Context[ServerSession, AppContext], app_name: str
) -> list[MemoryResult]:
    """Retrieve all relevant memories, past changes, and preferences for a tool."""
    return await queries.get_config_context(get_memory(ctx), app_name)


@mcp.tool(description="Search change history. Use to find specific past decisions.")
async def search_change_history(
    ctx: Context[ServerSession, AppContext], query: str, app_name: str | None = None
) -> list[MemoryResult]:
    """Find past decisions based on semantic search."""
    return await queries.search_change_history(get_memory(ctx), query, app_name)


@mcp.tool(
    description="Check dependencies. Find known dependencies or conflicts for a tool."
)
async def check_system_dependencies(
    ctx: Context[ServerSession, AppContext], tool_name: str
) -> list[MemoryResult]:
    """Query memory for recorded dependencies or conflicts."""
    return await queries.check_system_dependencies(get_memory(ctx), tool_name)


# --- Update Tools ---


@mcp.tool(
    description="Update memory entry. Use to correct incorrect or outdated information."
)
async def update_memory(
    ctx: Context[ServerSession, AppContext], memory_id: str, new_text: str
) -> Mem0UpdateResponse:
    """Edit a memory if it turns out to be wrong."""
    return await updates.update_memory(get_memory(ctx), memory_id, new_text)


# --- Work-in-Progress Tools ---


@mcp.tool(
    description="Save session state. Call at end of session if task NOT complete."
)
async def sync_work_in_progress(
    ctx: Context[ServerSession, AppContext],
    session_goal: str,
    modified_files: list[AppConfig],
    current_struggle: str,
) -> str:
    """Save mental state so next session can pick up where you left off."""
    return await queries.sync_work_in_progress(
        get_memory(ctx), session_goal, modified_files, current_struggle
    )


# --- Health Check Tools ---


@mcp.tool(description="Check server health and configuration status.")
async def health_check(ctx: Context[ServerSession, AppContext]) -> HealthStatus:
    """Verify all components are working."""
    app_ctx = ctx.request_context.lifespan_context
    return await health.health_check(app_ctx.config, app_ctx.memory)


# Register persona prompts
register_persona_prompts(mcp)


def main():
    """Entry pont for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
