"""Command Line Interface for manual dotfiles maintenance operations."""

import asyncio

import typer

from dotfiles_maintainer.config import ServerConfig
from dotfiles_maintainer.core.memory import MemoryManager
from dotfiles_maintainer.core.types import AppConfig, SystemMetadata
from dotfiles_maintainer.tools import baseline, drift, queries

app = typer.Typer()


def get_memory() -> MemoryManager:
    """Initialize a MemoryManager with default server configuration."""
    config = ServerConfig()
    return MemoryManager(config)


@app.command()
def drift_check():
    """Manually trigger config drift detection."""
    print("Checking for drift...")
    memory = get_memory()
    result = asyncio.run(drift.check_config_drift(memory))
    print(result)


@app.command()
def context(app_name: str):
    """Retrieve context for a specific app."""
    print(f"Retrieving context for {app_name}...")
    memory = get_memory()
    result = asyncio.run(queries.get_config_context(memory, app_name))
    print(result)


@app.command()
def init_baseline():
    """Initialize system baseline (Mocked Data)."""
    print("Initializing baseline with mock data...")
    memory = get_memory()

    config_map: list[AppConfig] = [
        {
            "app_name": "cli-test",
            "source_path": "~",
            "destination_path": "~",
            "file_structure": "monolithic",
            "dependencies": [],
        }
    ]
    sys_meta: SystemMetadata = {
        "os_version": "CLI-Test-OS",
        "main_shell": "Zsh",
        "main_terminal_emulator": "Terminal",
        "main_prompt_engine": "None",
        "main_editor": "Vim",
        "version_control": "git",
        "package_manager": "brew",
        "cpu": "Test-CPU",
        "extra": "",
    }

    result = asyncio.run(
        baseline.initialize_system_baseline(memory, "manual-cli", config_map, sys_meta)
    )
    print(result)


if __name__ == "__main__":
    app()
