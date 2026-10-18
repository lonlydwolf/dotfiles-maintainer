# API overview

This reference describes the retired prototype. Tool names are retained for compatibility with the historical implementation; their names and source docstrings sometimes imply stronger guarantees than the code provides. See [usage](usage.md) and [architecture](../ARCHITECTURE.md) for limitations. Input and response schemas are defined in [server.py](../src/dotfiles_maintainer/server.py) and [core/types.py](../src/dotfiles_maintainer/core/types.py).

## System and repository context

| Tool | Implemented behavior |
| --- | --- |
| `initialize_system_baseline` | Records supplied environment/configuration information; does not independently inventory the machine or select a target repository |
| `health_check` | Attempts memory search, detects VCS type, and checks key presence; does not verify a live LLM request |
| `check_config_drift` | Reads status in the server's working directory; no deployed-file comparison, with known Jujutsu and empty-memory-result errors |
| `ingest_version_history` | Sends recent VCS commit text from the process working directory to semantic memory |
| `commit_contextual_change` | Records a supplied change description/rationale; does not edit files or create a VCS commit |

## Memory and retrieval

| Tool | Implemented behavior |
| --- | --- |
| `get_config_context` | Searches memories for an application |
| `search_change_history` | Searches supplied terms and optional app name; results are semantic matches |
| `update_memory` | Replaces text for a supplied memory ID through the memory wrapper |
| `check_system_dependencies` | Searches recorded context for a tool name; does not inspect installed packages or resolve dependencies |
| `sync_work_in_progress` | Records supplied session goal, app names, and current difficulty; does not snapshot files |
| `log_troubleshooting_event` | Records a supplied error, cause, and fix |
| `get_troubleshooting_guide` | Searches recorded troubleshooting context |

## Planning and lifecycle notes

| Tool | Implemented behavior |
| --- | --- |
| `log_conceptual_roadmap` | Stores a supplied idea and priority |
| `query_roadmap` | Searches status/priority words; does not enforce those values as filters |
| `track_lifecycle_events` | Records supplied migration/removal context; does not alter installed tools |
| `manage_trial` | Records a trial intent and duration; does not schedule a timer or future action |
| `list_active_trials` | Searches for active-trial text; ignores `min_days_active` |

Memory text is processed with incomplete regex redaction before add/update; metadata is not scrubbed. Retrieval is approximate, and some errors are returned as empty results or text messages. Treat these interfaces as a record of the experiment, not an operational or security contract.
