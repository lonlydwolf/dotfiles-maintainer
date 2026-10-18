# Dotfiles Maintainer MCP

**Completed learning project · retired prototype · no active maintenance.**

I built this project to explore how an AI assistant could help maintain my dotfiles and remember the reasoning behind configuration decisions. It combines an MCP server, semantic memory, and Git/Jujutsu helpers. I owned the whole project; deciding which tools the assistant actually needed was the hardest part.

For my current workflow, having a model inspect my dotfiles and Git history has proved sufficient, so I no longer use this server. That is a personal workflow decision, not a claim that models can reliably reconstruct undocumented intent. The code and release history remain here as a learning artifact.

Read the [case study](docs/CASE_STUDY.md) for the motivation, design decisions, and retrospective. The latest historical release is [v1.0.1](https://github.com/lonlydwolf/dotfiles-maintainer/releases/tag/v1.0.1), published January 24, 2026. [Main CI at that revision](https://github.com/lonlydwolf/dotfiles-maintainer/actions/runs/21320410839) passed on Python 3.10–3.13; it does not establish current dependency or model compatibility.

## What the prototype implements

- MCP tools for recording supplied configuration changes, rationale, environment details, troubleshooting notes, and session context.
- Semantic retrieval through mem0, local Qdrant storage, and sentence-transformer embeddings, with an internal LLM used by the memory engine.
- Git/Jujutsu working-tree status and commit-history helpers.
- Pydantic input/response models, a Typer CLI, and unit tests plus temporary-repository integration tests.

The server does not edit or deploy dotfiles itself. The calling assistant supplies information and performs any file changes separately. Baseline metadata informs later retrieval; it is not an independently verified inventory.

## Important limits

This is an experimental memory companion, not a reliable configuration auditor or a security boundary. Do not feed it secrets or sensitive raw configuration.

- **Redaction is incomplete.** Private-key bodies and some structured credential values can survive the regex helper. Metadata is passed to the memory engine without redaction. Configured remote providers may receive submitted content.
- **Repository selection follows the server's working directory.** Launching with `uv --directory /path/to/dotfiles-maintainer` checks this server checkout, not a separate dotfiles repository. There is no configured dotfiles-root setting, and no comparison of deployed home files with a manager's source state.
- **Status reporting has known errors.** Clean Jujutsu status prose can be reported as changes. An empty memory-write result can turn a detected change into an error with no file details.
- **Semantic retrieval is approximate.** Roadmap status/priority are search terms rather than enforced filters; `list_active_trials` ignores its minimum-age argument. These tools are not an authoritative task or lifecycle database.

These limits were documented during the later closeout review; they are not fixes in the code. See [architecture](ARCHITECTURE.md), [usage](docs/usage.md), and [security notes](SECURITY.md) before reproducing the experiment.

## Historical setup

For inspection or a fork, the project declares Python 3.10+ and uses `uv`:

```bash
git clone https://github.com/lonlydwolf/dotfiles-maintainer.git
cd dotfiles-maintainer
uv sync
```

Dependency installation and model downloads may be substantial. The lockfile and historical tests do not guarantee that a fresh environment or current provider API works unchanged.

The explicit configuration names are:

| Variable | Purpose |
| --- | --- |
| `DOTFILES_USER_ID` | Memory partition; defaults to `$USER` |
| `DOTFILES_MEMORY_PATH` | Local Qdrant path; defaults to `~/.dotfiles-mcp/qdrant` |
| `DOTFILES_LLM_PROVIDER` | `gemini`, `openai`, `anthropic`, or `ollama` |
| `DOTFILES_LLM_KEY` | Explicit provider key; the unprefixed `LLM_KEY` is **not** read |
| `LLM_MODEL` | Explicit model name; verify availability with the provider |
| `DOTFILES_VCS_TIMEOUT` | VCS timeout in seconds; defaults to 10 |
| `LOG_LEVEL` | Logging level; defaults to `INFO` |

**Configuration precedence caveat:** using `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OLLAMA_BASE_URL` for autodetection overwrites the provider and model, even when `LLM_MODEL` is set. A nonempty `DOTFILES_LLM_KEY` bypasses that autodetection. Set the explicit provider, key, and model together for a hosted-provider experiment. Historical defaults are not current model recommendations. Ollama custom endpoint handling is incomplete; see the [usage guide](docs/usage.md).

For a synthetic experiment, an MCP client can launch `dotfiles-mcp` through `uv run`; [usage](docs/usage.md) explains process-directory implications. Avoid applying the old installation-directory launch pattern to real dotfiles.

## Exploring the source

```text
src/dotfiles_maintainer/
├── core/       # Memory wrapper and typed data models
├── tools/      # MCP tool implementations
├── prompts/    # Persona and memory-extraction prompts
├── utils/      # VCS helpers and best-effort redaction
├── config.py   # Environment settings and memory configuration
├── server.py   # MCP registration and lifespan
└── cli.py      # Manual inspection commands
```

[API reference](docs/api.md) · [Fork/development notes](CONTRIBUTING.md) · [Historical release policy](RELEASE_POLICY.md) · [Changelog](CHANGELOG.md)

Licensed under [Apache 2.0](LICENSE).
