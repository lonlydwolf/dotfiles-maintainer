# Release Policy

This document outlines the release process and versioning strategy for the Dotfiles Maintainer project.

## Versioning Strategy

We adhere to [Semantic Versioning (SemVer) 2.0.0](https://semver.org/).

**Format:** `MAJOR.MINOR.PATCH`

*   **MAJOR**: Incompatible API changes (e.g., removing a tool, changing tool arguments breaking backward compatibility).
*   **MINOR**: Functionality added in a backward-compatible manner (e.g., adding a new tool, new optional parameters).
*   **PATCH**: Backward-compatible bug fixes (e.g., fixing regex, updating dependencies).

## Release Cadence

*   **Feature Releases (Minor):** Bi-weekly or when significant new features are ready and tested.
*   **Bug Fixes (Patch):** As needed, immediately for critical bugs.
*   **Security Fixes:** Immediate priority release.

## Branching Model

We use a simplified workflow compatible with both standard Git and Jujutsu (`jj`):

*   `main`: The stable, production-ready branch.
*   **Features:** Developed in ephemeral branches (Git) or anonymous revisions (jj) before being finalized into a named branch for PR.

### Release Workflow

1.  **Work:** Finalize the code changes.
2.  **Branch:** Ensure `main` is up to date and clean.
3.  **Verify:** CI checks must pass.
4.  **Tag:** Create a git tag (e.g., `v1.2.0`) on `main`.

## Deprecation Policy

Before removing a feature/tool:
1.  Mark it as `[DEPRECATED]` in the tool description and docstring.
2.  Add a warning log in the code.
3.  Wait for at least one MINOR release cycle before removing it in the next release.
