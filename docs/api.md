# API Reference

## Tools

### System
*   `initialize_system_baseline`: Establish ground truth for the environment.
*   `health_check`: Check server health and configuration status.

### Version Control & History
*   `check_config_drift`: Detect configuration drift between filesystem and VCS.
*   `ingest_version_history`: Backfill memory with VCS history.
*   `commit_contextual_change`: Log config change with semantic context.

### Memory & Context
*   `get_config_context`: Get context for an app before modifying it.
*   `search_change_history`: Search change history for past decisions.
*   `update_memory`: Correct incorrect or outdated memory entries.

### Planning & Lifecycle
*   `log_conceptual_roadmap`: Store future ideas.
*   `query_roadmap`: Retrieve roadmap items.
*   `track_lifecycle_events`: Track tool migration/removal.
*   `manage_trial`: Start tool/plugin trial.
*   `list_active_trials`: List active trials.

### Troubleshooting
*   `log_troubleshooting_event`: Log a bug fix.
*   `get_troubleshooting_guide`: Search troubleshooting history.
