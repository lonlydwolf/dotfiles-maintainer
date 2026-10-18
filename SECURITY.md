# Security and support status

Dotfiles Maintainer is a retired learning prototype. No version is actively supported, and there is no promised response timeline or security-fix release schedule. The historical `1.x` releases should not be treated as production-ready software.

## Sensitive data

Do not submit secrets or sensitive raw configuration to this server. `redact_secrets()` is a best-effort regex helper, not a security boundary: private-key bodies and some structured credential values can remain intact. Metadata bypasses this helper. Data passed to the memory engine may be processed by the configured remote LLM even though Qdrant storage is local.

The working-tree status tool is not a security scanner or a check for unauthorized changes. It follows process working directory and has documented reporting limitations. The CLI also includes memory-reset operations; use disposable data when exploring the code. Configuration values are not a secret-masking interface, so do not share configuration dumps containing credentials.

See [architecture](ARCHITECTURE.md) and [usage](docs/usage.md) for the actual data flow and limitations. The closeout review used synthetic data and did not establish that any real secret exposure occurred.

## Reporting an issue

Do not post credentials, private dotfiles, or exploitable personal configuration in a public issue. If contacting the author, use the contact address in [package metadata](pyproject.toml), or private GitHub security reporting if available. There is no guarantee of triage or a fix for this retired project.

A fork intended for real use needs its own support policy, dependency review, tested data-handling contract, and operational validation.
