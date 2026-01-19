# Dotfiles Maintainer MCP

[![CI](https://github.com/lonlydwolf/dotfiles-maintainer/actions/workflows/ci.yml/badge.svg)](https://github.com/lonlydwolf/dotfiles-maintainer/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dotfiles-maintainer.svg)](https://pypi.org/project/dotfiles-maintainer/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](#testing)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)

**An AI-native MCP server for managing configuration files with semantic memory, context awareness, and strict drift detection.**

---

## 🚀 Key Features

*   **🧠 Semantic Memory:** Remembers *why* changes were made, not just *what* changed.
*   **🛡️ Drift Detection:** Prevents configuration rot by detecting uncommitted changes at session start.
*   **🖥️ Hardware Aware:** Adapts suggestions based on system metadata (OS, CPU, Shell).
*   **🔒 Secure by Default:** Automatically redacts API keys and secrets before storing memories.
*   **🔌 Modular & Extensible:** Built on `FastMCP` (via official SDK) with a plugin-ready architecture.

---

## 📦 Installation

### Prerequisites

*   **Python 3.10+**
*   **uv** (Fast Python package installer)

If you don't have `uv` installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step-by-Step Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/lonlydwolf/dotfiles-maintainer.git
    cd dotfiles-maintainer
    ```
    *Note: This project also supports [Jujutsu (jj)](https://github.com/martinvonz/jj) for version control.*

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Environment Configuration:**
    The server requires the following environment variables for memory operations:

    | Variable | Description | Default |
    |----------|-------------|---------|
    | `DOTFILES_USER_ID` | Unique ID for memory partitioning | Current `$USER` |
    | `DOTFILES_LLM_PROVIDER` | `openai`, `anthropic`, `gemini`, or `ollama` | `gemini` |
    | `LLM_KEY` | API Key for the chosen provider | (Required) |
    | `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | `INFO` |

---

## 🛠️ MCP Client Configuration

To use this server with an MCP-compliant client, configure it to run via `uv`.

### Generic Configuration Pattern
Most clients require a configuration similar to this:

**Command:** `uv`
**Arguments:** `--directory /absolute/path/to/dotfiles-maintainer run dotfiles-mcp`
**Environment Variables:**
*   `LLM_KEY`: your-api-key
*   `DOTFILES_USER_ID`: your-username

### Implementation Examples

#### Gemini CLI
Add to your `config.yaml` or relevant settings:
```yaml
mcpServers:
  dotfiles-maintainer:
    command: uv
    args: ["--directory", "/path/to/repo", "run", "dotfiles-mcp"]
    env:
      LLM_KEY: "..."
      DOTFILES_USER_ID: "..."
```

#### Claude Desktop / Claude Code
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "dotfiles-maintainer": {
      "command": "uv",
      "args": ["--directory", "/path/to/repo", "run", "dotfiles-mcp"],
      "env": {
        "LLM_KEY": "...",
        "DOTFILES_USER_ID": "..."
      }
    }
  }
}
```

#### IDE Extensions (Cursor / Continue)
Configure as an "External MCP Server" using the generic command pattern above.

---

## 🧪 Testing

We use `pytest` for unit and integration testing.

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=dotfiles_maintainer
```

---

## 🔄 Version Control Workflow

This project is managed with **Jujutsu (jj)**, but fully supports standard Git workflows.

*   **Primary VCS:** [Jujutsu (jj)](https://github.com/martinvonz/jj)
*   **Compatibility:** Fully compatible with `git` commands.

---

## 🏗️ Architecture

The project follows a modular architecture:

```
src/dotfiles_maintainer/
├── core/           # Shared logic (Memory, Types)
├── tools/          # Individual MCP tools (Drift, History, etc.)
├── prompts/        # System Persona & Workflows
└── utils/          # VCS & Security helpers
```

---

## 💻 Development & Contributing

We welcome contributions! Please check [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

### Using Templates
Use the provided templates in the `Templates/` directory:
*   **Tools:** `Templates/tool.py.template`
*   **Resources:** `Templates/resource.py.template`
*   **Prompts:** `Templates/prompt.py.template`

### Adding a New Tool
1.  Copy `Templates/tool.py.template` to `src/dotfiles_maintainer/tools/your_tool.py`.
2.  Implement logic using `MemoryManager`.
3.  Register the tool in `src/dotfiles_maintainer/server.py`.

---

## 🔍 Troubleshooting

*   **`uv: command not found`:** Ensure `uv` is in your PATH after installation.
*   **Database Errors:** Ensure `~/.dotfiles-mcp/qdrant` is writable.
*   **Relative Paths:** Always use **absolute paths** in MCP client configurations.

---

## ✅ Development Status

**Completed:**
- [x] Modular Refactoring
- [x] Core Tools Implementation
- [x] Health Check Tool
- [x] Manual Testing CLI

**Next Steps:**
- [ ] Backup & Restore (`export_memory_backup`)
- [ ] Secrets Scanning (`scan_for_uncommitted_secrets`)

---

**License:** Apache 2.0
