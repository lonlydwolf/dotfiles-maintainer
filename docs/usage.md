# Usage Guide

## Running the Server

### Via `uv` (Recommended)

```bash
uv run dotfiles-mcp
```

### Via MCP Client

Configure your client (Claude Desktop, etc.) to run the server using `uv`. See the `README.md` for specific configuration examples.

## Core Workflows

### 1. Initialization
When setting up on a new machine, run:
- `initialize_system_baseline`: Captures OS, shell, and hardware details.

### 2. Daily Routine
At the start of a session:
- `check_config_drift`: Verifies if your local files match the git repository.
- `query_roadmap`: Checks for pending tasks or ideas.

### 3. Making Changes
When you edit a dotfile:
1. Make the change locally.
2. Run `commit_contextual_change`: Logs *why* you made the change (e.g., "Improved startup time by 200ms").

### 4. Troubleshooting
If something breaks:
- `health_check`: Verifies server components.
- `search_change_history`: Finds past changes related to the broken tool.
- `get_troubleshooting_guide`: Checks if this issue was solved before.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DOTFILES_USER_ID` | User identifier (defaults to `$USER`) |
| `DOTFILES_MEMORY_PATH` | Path to Qdrant DB (default: `~/.dotfiles-mcp/qdrant`) |
| `LLM_KEY` | API Key for the LLM provider |
| `DOTFILES_VCS_TIMEOUT` | Timeout for git/jj commands (default: 10s) |
