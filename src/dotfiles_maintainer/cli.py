"""Command Line Interface for Dotfiles Maintainer."""

import asyncio
import atexit
import json
import logging
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from dotfiles_maintainer.config import ServerConfig
from dotfiles_maintainer.core.memory import MemoryManager
from dotfiles_maintainer.server import mcp  # Import the MCP instance to access tools
from dotfiles_maintainer.tools import drift

# --- Setup ---

app = typer.Typer(
    name="dotfiles-cli",
    help="CLI for managing the Dotfiles Maintainer MCP server and memory.",
    add_completion=False,
)
console = Console()

# Sub-commands
memory_app = typer.Typer(name="memory", help="Inspect and manage semantic memory.")
config_app = typer.Typer(name="config", help="View and manage configuration.")
system_app = typer.Typer(name="system", help="System diagnostics and drift detection.")
tools_app = typer.Typer(name="tools", help="Interact with registered MCP tools.")

app.add_typer(memory_app)
app.add_typer(config_app)
app.add_typer(system_app)
app.add_typer(tools_app)


# --- Asyncio Management ---

_loop: asyncio.AbstractEventLoop | None = None


def get_loop() -> asyncio.AbstractEventLoop:
    """Get or create the global event loop."""
    global _loop
    if _loop is None:
        try:
            _loop = asyncio.get_running_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    return _loop


def shutdown_loop():
    """Cleanup the event loop on exit."""
    global _loop
    if _loop and not _loop.is_closed():
        # Cancel all running tasks
        pending = asyncio.all_tasks(_loop)
        for task in pending:
            task.cancel()

        # Allow tasks to finish cancelling
        if pending:
            try:
                _loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            except Exception:
                pass

        # Shutdown async generators
        try:
            _loop.run_until_complete(_loop.shutdown_asyncgens())
        except Exception:
            pass

        # Finally close
        _loop.close()


atexit.register(shutdown_loop)


def run_async(coro):
    """Run a coroutine using the shared event loop."""
    loop = get_loop()
    return loop.run_until_complete(coro)


# --- Helpers ---


def get_memory() -> MemoryManager:
    """Initialize a MemoryManager with default server configuration."""
    config = ServerConfig()
    return MemoryManager(config)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
):
    """Dotfiles Maintainer CLI."""
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=log_level)


# --- Memory Commands ---


@memory_app.command("inspect")
def memory_inspect(
    query: str = typer.Argument(..., help="Search query to inspect memory."),
    limit: int = typer.Option(5, help="Number of results to return."),
):
    """Semantic search in the memory store."""
    console.print(f"[bold blue]Searching memory for:[/bold blue] '{query}'")
    manager = get_memory()
    try:
        results = run_async(manager.search(query, limit=limit))
        if not results.results:
            console.print("[yellow]No matching memories found.[/yellow]")
            return

        table = Table(title=f"Search Results ({len(results.results)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Memory", style="white")
        table.add_column("Score", style="green")

        for mem in results.results:
            # Handle both dict and object access if model usage varies
            mem_id = getattr(mem, "id", None) or mem.id or "N/A"
            text = getattr(mem, "memory", None) or mem.memory or "N/A"
            score = getattr(mem, "score", None) or mem.score or 0.0
            table.add_row(str(mem_id), str(text), f"{score:.2f}")

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@memory_app.command("facts")
def memory_facts(
    limit: int = typer.Option(20, help="Limit the number of facts displayed."),
):
    """List all extracted facts/memories."""
    console.print("[bold blue]Retrieving all memories...[/bold blue]")
    manager = get_memory()
    try:
        memories = run_async(manager.get_all(limit=limit))
        if not memories.results:
            console.print("[yellow]No memories found.[/yellow]")
            return

        table = Table(title="Stored Facts")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Fact", style="white")

        for mem in memories.results:
            # 'mem' is likely a dict from mem0
            mem_id = mem.id or "N/A"
            text = mem.memory or "N/A"
            table.add_row(str(mem_id), str(text))

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@memory_app.command("clear")
def memory_clear(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation."
    ),
):
    """Clear all memories (Reset)."""
    if not force:
        if not typer.confirm("Are you sure you want to DELETE ALL memories?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return

    console.print("[bold red]Clearing all memories...[/bold red]")
    manager = get_memory()
    try:
        run_async(manager.reset())
        console.print("[green]Memory reset successfully.[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# --- Config Commands ---


@config_app.command("show")
def config_show():
    """Show current server configuration."""
    config = ServerConfig()
    console.print(f"[bold]Config Source:[/bold] {config.model_dump_json(indent=2)}")


@config_app.command("path")
def config_path():
    """Show configuration file paths."""
    # This assumes .env or standard paths.
    console.print(f"[bold]Working Directory:[/bold] {Path.cwd()}")
    # If ServerConfig loads from a specific file, we could list it here.
    console.print(
        "[dim]Configuration is loaded from environment variables and defaults.[/dim]"
    )


# --- System Commands ---


@system_app.command("info")
def system_info():
    """Display system information."""
    info = {
        "System": platform.system(),
        "Node": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python": sys.version,
    }
    table = Table(title="System Info")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    for k, v in info.items():
        table.add_row(k, str(v).replace("\n", " "))
    console.print(table)


@system_app.command("drift")
def system_drift():
    """Check for configuration drift."""
    console.print("[bold blue]Checking for config drift...[/bold blue]")
    manager = get_memory()
    try:
        # We need to manually invoke drift.check_config_drift.
        # Note: server.py passes timeout from config, we should too.
        config = ServerConfig()
        result = run_async(
            drift.check_config_drift(manager, timeout=config.vcs_timeout)
        )

        console.print(f"[bold]Status:[/bold] {result.status}")
        if result.status == "modified":
            console.print("[red]Drift Detected:[/red]")
            console.print(f" - {result.message}")
        elif result.status == "clean":
            console.print("[green]System is in sync.[/green]")
        else:
            console.print("[bold red] Status: Error[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@system_app.command("health")
def system_health():
    """Check server health."""
    console.print("[bold blue]Checking system health...[/bold blue]")
    # Import health module locally to avoid circular deps if any
    from dotfiles_maintainer.tools import health

    manager = get_memory()
    config = ServerConfig()

    try:
        result = run_async(health.health_check(config, manager))

        status_color = "green" if result.status == "healthy" else "red"
        console.print(
            f"[bold]Status:[/bold] [{status_color}]{result.status}[/{status_color}]"
        )

        table = Table(title="Component Health")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Message", style="dim")

        for k, v in result.components.items():
            comp_color = "green" if v else "red"
            table.add_row(k, f"[{comp_color}]{v}[/{comp_color}]", "")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# --- Tools Commands ---


@tools_app.command("list")
def tools_list():
    """List all registered MCP tools."""
    # Access the tool manager from the FastMCP instance
    # Note: Accessing private member _tool_manager might be brittle but necessary for CLI
    try:
        # FastMCP stores tools in _tool_manager (based on library inspection)
        # or we can iterate if a public method exists.
        # mcp.list_tools() returns list[Tool] in standard MCP SDK,
        # but FastMCP wraps it.

        # We'll try to access the internal registry if public API is missing
        tools = getattr(mcp, "_tool_manager", None)
        if not tools:
            # Fallback: check if mcp itself is iterable or has tools property
            console.print("[yellow]Could not access tool registry directly.[/yellow]")
            return

        # tools._tools is usually a dict of name -> Tool object
        tool_registry = getattr(tools, "_tools", {})

        table = Table(title="Registered MCP Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")

        for name, tool in tool_registry.items():
            desc = getattr(tool, "description", "No description")
            table.add_row(name, desc)

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing tools:[/bold red] {e}")


# --- Tool Execution Helpers ---


@dataclass
class MockLifespan:
    config: ServerConfig
    memory: MemoryManager


@dataclass
class MockRequest:
    lifespan_context: MockLifespan


@dataclass
class MockContext:
    request_context: MockRequest

    def info(self, msg: str):
        logging.info(msg)

    def error(self, msg: str):
        logging.error(msg)

    def warning(self, msg: str):
        logging.warning(msg)

    def debug(self, msg: str):
        logging.debug(msg)


@tools_app.command(
    "run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def tools_run(
    ctx: typer.Context,
    tool_name: str = typer.Argument(..., help="Name of the tool to run."),
):
    """Run a specific MCP tool with arguments (e.g. key=value)."""

    # 1. Find the tool
    tools_mgr = getattr(mcp, "_tool_manager", None)
    if not tools_mgr:
        console.print("[red]Could not access tool registry.[/red]")
        return

    tool_registry = getattr(tools_mgr, "_tools", {})
    tool = tool_registry.get(tool_name)

    if not tool:
        console.print(f"[red]Tool '{tool_name}' not found.[/red]")
        console.print("Use 'tools list' to see available tools.")
        return

    # 2. Parse Arguments
    # ctx.args contains ["key=value", "--flag", ...]
    # We support key=value mainly.
    kwargs = {}
    for arg in ctx.args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            # Basic type inference
            if v.lower() == "true":
                v = True
            elif v.lower() == "false":
                v = False
            elif v.isdigit():
                v = int(v)
            # Remove leading -- if present
            k = k.lstrip("-")
            kwargs[k] = v
        else:
            console.print(
                f"[yellow]Ignored argument '{arg}'. Use key=value format.[/yellow]"
            )

    console.print(f"[bold blue]Running {tool_name}...[/bold blue]")
    if kwargs:
        console.print(f"Args: {kwargs}")

    # 3. Create Mock Context
    config = ServerConfig()
    memory = MemoryManager(config)
    mock_ctx = MockContext(
        request_context=MockRequest(
            lifespan_context=MockLifespan(config=config, memory=memory)
        )
    )

    # 4. Execute
    try:
        # tool.fn is the decorated async function
        # We need to pass ctx as first arg if the tool expects it.
        # fastmcp tools usually expect ctx as first arg.
        result = run_async(tool.fn(mock_ctx, **kwargs))

        console.print("[green]Result:[/green]")

        def serialize_result(res: Any) -> Any:
            """Recursively serialize Pydantic models."""
            if hasattr(res, "model_dump"):
                return res.model_dump(mode="json")
            if isinstance(res, list):
                return [serialize_result(item) for item in res]
            if isinstance(res, dict):
                return {k: serialize_result(v) for k, v in res.items()}
            return res

        console.print_json(json.dumps(serialize_result(result), default=str))

    except TypeError as e:
        console.print(f"[bold red]Argument Error:[/bold red] {e}")
        console.print(
            "Check that you provided the correct arguments in key=value format."
        )
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")


if __name__ == "__main__":
    app()
