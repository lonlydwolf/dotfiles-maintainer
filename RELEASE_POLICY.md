# Historical release policy

This project is retired. No releases, maintenance cadence, compatibility window, or security-response timeline are promised. `main` contains the learning prototype and should not be read as a production-ready branch.

The latest historical release is [v1.0.1](https://github.com/lonlydwolf/dotfiles-maintainer/releases/tag/v1.0.1), published January 24, 2026. See [CHANGELOG.md](CHANGELOG.md) for recorded changes. Historical tags describe that source at that time; they do not guarantee that present-day dependencies or provider models remain compatible.

## Conventions retained for reference

The project used `MAJOR.MINOR.PATCH` version numbers with the intended semantic-versioning distinction between incompatible changes, additive features, and fixes. The documented workflow was to develop a change in Git or Jujutsu, verify it, and tag the release on `main`.

For a maintained fork, define a new release policy based on its actual users and support capacity. Before releasing, validate installation, tool contracts, configuration precedence, repository targeting, sensitive-data handling, and the selected provider. Passing unit tests alone is not a production-readiness claim.
