# Development notes for a retired project

Dotfiles Maintainer is a completed learning project with no active maintenance or solicitation of feature contributions. Issues and pull requests may not be reviewed. The source remains available under the [Apache 2.0 license](LICENSE) for inspection and independent forks.

Start with the [case study](docs/CASE_STUDY.md), [architecture](ARCHITECTURE.md), and [security notes](SECURITY.md). They explain the implemented boundaries and unresolved limitations.

## Historical local setup

From a checkout or your own fork, with `uv` available:

```bash
uv sync
uv run python -m pytest tests/
```

These are the project's existing development commands, not a claim that the current dependency set has been revalidated. Tests include mocks and temporary Git/Jujutsu repositories; Jujutsu tests can skip if its binary is absent. Avoid live credentials and use disposable memory storage and repositories for experiments.

Useful checks when developing a fork:

```bash
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```

Lint/type tools are declared in the development dependencies. Their presence here does not imply the historical CI enforced all of them or that the existing code passes every check.

## Tests worth adding before extending a fork

- Environment-variable loading and preservation of explicit provider/model choices.
- Separate server installation and target repositories, plus clean and dirty Git/Jujutsu states.
- Empty memory results and provider failures that preserve already-known local status.
- Synthetic secret fixtures covering complete blocks and structured data, including metadata.
- Deterministic age/status/category semantics wherever a tool promises filtering.

The historical project used Conventional Commit-style messages and both Git and Jujutsu. [The Jujutsu reference](docs/jj_cli_reference.md) is retained as a historical aid; check commands against your installed version. New tools are implemented in `tools/` and registered in `server.py`, but a fork should establish its core workflow before expanding the tool catalog.
