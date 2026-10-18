# Historical usage guide

This is a retired prototype. The instructions below explain the implementation for inspection or a fork, not a supported setup for personal dotfiles. Read [limitations](../README.md#important-limits) and [security notes](../SECURITY.md) first. Use synthetic data, a disposable repository, and a separate memory path.

## Configuration

| Variable | Meaning |
| --- | --- |
| `DOTFILES_USER_ID` | Memory partition identifier; defaults to `$USER` |
| `DOTFILES_MEMORY_PATH` | Qdrant path; defaults to `~/.dotfiles-mcp/qdrant` |
| `DOTFILES_LLM_PROVIDER` | `gemini`, `openai`, `anthropic`, or `ollama`; defaults to `gemini` |
| `DOTFILES_LLM_KEY` | Explicit key setting; unprefixed `LLM_KEY` is ignored |
| `LLM_MODEL` | Model identifier; historical default is `gemini-2.5-flash-lite-preview-09-2025` |
| `DOTFILES_VCS_TIMEOUT` | Git/Jujutsu timeout in seconds; defaults to 10 |
| `LOG_LEVEL` | Log level; defaults to `INFO` |

For a hosted-provider experiment, set `DOTFILES_LLM_PROVIDER`, a nonempty `DOTFILES_LLM_KEY`, and `LLM_MODEL` together. Verify that the selected provider supports the chosen model; the historical defaults are not current recommendations.

If `DOTFILES_LLM_KEY` is empty, autodetection checks `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, then `OLLAMA_BASE_URL`, and replaces both provider and model with hardcoded choices. This overwrites `LLM_MODEL`; for example, `GEMINI_API_KEY` selects `gemini-2.0-flash`. Do not rely on provider autodetection to preserve explicit settings.

The Ollama path constructs a model-only LLM configuration and does not explicitly forward the configured base URL. Custom endpoint behavior is therefore not a validated feature of this wrapper. The backup/secrets-scan toggles in configuration do not implement backup or scanning tools.

## Process directory matters

The historical command, run from this checkout, is:

```bash
uv run dotfiles-mcp
```

An MCP client can launch that same command, but the process working directory is the repository inspected by the status/history helpers. `uv --directory /path/to/dotfiles-maintainer run dotfiles-mcp` deliberately changes into the server checkout; it does **not** select separate dotfiles. The baseline tool records supplied paths but does not use them to retarget these helpers. There is no explicit dotfiles-root setting.

For a fork, establish an explicit target-directory contract and test it. Until then, inspect status directly in the intended disposable repository instead of treating this tool's output as validation of your deployed configuration.

## Implemented workflows

1. **Record context:** `initialize_system_baseline` stores assistant-supplied OS, shell, hardware, and configuration information. It does not discover or verify that inventory.
2. **Record a change:** an assistant edits a file separately, then passes a description and rationale to `commit_contextual_change`. The tool records context; it does not commit or deploy the file change.
3. **Retrieve context:** `get_config_context`, `search_change_history`, and `get_troubleshooting_guide` perform semantic retrieval. Returned memories may be incomplete, approximate, or stale.
4. **Inspect working-tree status:** `check_config_drift` reads Git/Jujutsu status. It does not compare home files with a dotfiles manager's source, clean Jujutsu output can be misclassified, and memory-write failures/empty results can obscure detected changes.
5. **Record plans:** roadmap and trial tools store notes. Roadmap status/priority are search phrases; the active-trial age argument is ignored. No reliable scheduling or deterministic lifecycle tracking is provided.

`health_check` attempts a memory search, detects a VCS type, and checks whether a provider key is configured. It does not prove that a live LLM call succeeds, that the correct target repository was selected, or that all binaries and subsystems are usable.

The CLI includes destructive memory administration. `memory clear` invokes a reset affecting all users in the configured store, not only the selected partition. Use only disposable storage when exploring it, and do not publish configuration output containing credentials.

See the [API overview](api.md) for the registered tools and [development notes](../CONTRIBUTING.md) for checks on a fork.
