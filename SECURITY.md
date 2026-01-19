# Security Policy

## Supported Versions

We support the latest major version of the Dotfiles Maintainer MCP server.

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please **DO NOT** create a public GitHub issue.

Instead, please report it via email to the maintainer (or via a private GitHub security advisory if enabled).

### What to Include:
*   A description of the vulnerability.
*   Steps to reproduce the issue.
*   Potential impact.

### Response Timeline:
*   We will acknowledge receipt of your report within 48 hours.
*   We will provide a timeline for a fix within 1 week.
*   We will notify you once the fix is released.

## Sensitive Data Handling

This project is designed to handle configuration files which may inadvertently contain secrets.
*   We employ `redact_secrets()` utility to scrub known patterns before storing data in memory.
*   However, no regex is perfect. Users are responsible for ensuring their dotfiles do not contain hardcoded secrets.
