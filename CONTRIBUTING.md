# Contributing to Dotfiles Maintainer

Thank you for your interest in contributing! We welcome all contributions that help make this MCP server more robust, secure, and useful.

## 🛠️ Development Setup

This project uses `uv` for ultra-fast dependency management.

1.  **Install uv:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone & Sync:**
    ```bash
    git clone https://github.com/yourusername/dotfiles-maintainer.git
    cd dotfiles-maintainer
    uv sync
    ```

3.  **Activate Environment:**
    ```bash
    source .venv/bin/activate
    ```

## 🧪 Testing & Quality

We enforce strict quality standards. Please run these checks before submitting a PR.

### Run Tests
```bash
uv run python -m pytest tests/
```
*Requirement: 100% pass rate.*

### Linting & Formatting
```bash
uv run ruff check .
uv run ruff format .
```
*Requirement: Zero warnings/errors.*

### Type Checking
```bash
uv run basedpyright
```
*Requirement: Zero errors.*

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

**Format:** `<type>(<scope>): <subject>`

**Types:**
*   `feat`: New feature (e.g., adding a new tool)
*   `fix`: Bug fix
*   `docs`: Documentation only changes
*   `style`: Formatting, missing semi-colons, etc.
*   `refactor`: Code change that neither fixes a bug nor adds a feature
*   `test`: Adding missing tests or correcting existing tests
*   `chore`: Changes to the build process or auxiliary tools

**Example:**
`feat(drift): add support for jujutsu vcs detection`

## 🚀 Pull Request Process

We recommend using **Jujutsu (jj)** for managing contributions, but standard Git is also accepted.

### Using Jujutsu (Recommended)
1.  **Start work:** `jj new main`
2.  **Iterate:** Make changes and use `jj describe` to set the commit message.
3.  **Branch:** Create a bookmark: `jj bookmark create feat/my-feature`
4.  **Push:** `jj git push`
5.  See [docs/jj_cli_reference.md](docs/jj_cli_reference.md) for a detailed cheat sheet.

### Using Git (Alternative)
1.  Create a new branch from `main`: `git checkout -b feat/my-feature`
2.  Commit your changes: `git commit -m "feat: description"`
3.  Push to origin: `git push origin feat/my-feature`

### Checklist
1.  Ensure all tests pass: `uv run python -m pytest tests/`
2.  Ensure no linting errors: `uv run ruff check .`
3.  Submit the PR with a clear description of the "Why" and "What".

## 🏗️ Architecture

Please familiarize yourself with our modular architecture before contributing code. All new tools should reside in `src/dotfiles_maintainer/tools/` and be registered in `server.py`.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.
