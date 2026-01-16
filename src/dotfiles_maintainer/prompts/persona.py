"""MCP prompts for DotMate persona."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent


def dotmate_persona() -> list[PromptMessage]:
    """Load the full DotMate persona from Persona.md."""
    persona_path = (Path(__file__).parent.parent.parent / "Persona.md").resolve()

    with open(persona_path, "r") as f:
        content = f.read()

    return [
        PromptMessage(role="assistant", content=TextContent(type="text", text=content))
    ]


def session_start() -> list[PromptMessage]:
    """Workflow for starting a new session."""
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text="""🔍 **Session Start Workflow**

                1. Run check_config_drift()
                2. Run validate_memory_integrity() (when implemented)
                3. Check for incomplete WIP
                4. Ask user: "What would you like to work on today?

                Follow DotMATE persona guidelines for all interactions.""",
            ),
        )
    ]


def pre_change() -> list[PromptMessage]:
    """Safety checklist before modifications."""
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text="""⚠️ **Pre-Change Safety Checklist**

                Before proceeding:

                ✅ 1. Search memory: get_config_context() + search_change_history()
                ✅ 2. Check conflicts: Was this tried before? Any failures?
                ✅ 3. Scan secrets: scan_for_uncommitted_secrets() (when implemented)
                ✅ 4. Backup if risky: export_memory_backup() (when implemented)""",
            ),
        )
    ]


def register_persona_prompts(mcp: FastMCP) -> None:
    """Register all persona-related prompts."""
    mcp.prompt(
        name="system-persona",
        description="Complete DotMate system persona - load this to understand your role",
    )(dotmate_persona)

    mcp.prompt(
        name="session-start",
        description="Session initialization checklist",
    )(session_start)

    mcp.prompt(
        name="pre-change",
        description="Checklist before making any config change",
    )(pre_change)
