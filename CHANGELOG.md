# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-24

### Added
- **CLI**: Complete rewrite with `typer` and `rich` tables
- **Core**: Administrative memory operations (`get_all`, `delete_all`, `reset`)
- **Config**: Multi-provider LLM support (OpenAI, Anthropic, Ollama) and prompt templates
- **Documentation**: Architecture documentation (`ARCHITECTURE.md`)
- **Resources**: Updated tech stack and MCP tools registry

### Changed
- **Refactor**: Migrated all internal types and tools to Pydantic models for validation
- **Tools**: Enhanced output formatting with emojis and metadata logging

### Fixed
- Test suite compatibility with Pydantic models (achieved 99% coverage)
- CLI type safety and mutable default arguments
- `MemoryConfig` Qdrant on-disk persistence
- Version consistency in `pyproject.toml`
- Various dependency updates and CI improvements

## [1.0.0] - 2026-01-18

### Added
- Initial public release
- 15 MCP tools for dotfiles management
- Semantic memory via mem0
- Support for Git and Jujutsu VCS
- Configuration drift detection
- System baseline initialization
