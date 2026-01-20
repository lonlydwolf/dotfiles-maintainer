"""Core Data Structures and Types."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, JsonValue


class MemoryResult(BaseModel):
    """A single search result from the memory vector store.

    Attributes:
        id: Unique memory identifier (UUID)
        memory: The actual text content stored
        score: Similarity score (0.0 to 1.0, higher is more relevant)
        metadata: Additional structured data attached to this memory
        created_at: ISO 8601 timestamp of creation
        updated_at: ISO 8601 timestamp of last modification

    """

    id: str
    memory: str
    score: float
    metadata: dict[str, JsonValue] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SearchResult(BaseModel):
    """Response from a memory search operation.

    Attributes:
        results: List of matching memories, ordered by relevance
        relations: Optional graph relationships between memories

    """

    results: list[MemoryResult] = Field(default_factory=list)
    relations: list[JsonValue] | None = None


class SearchResultWithGraph(BaseModel):
    """Extended search result when graph store is enabled."""

    results: list[MemoryResult] = Field(default_factory=list)
    relations: list[dict[str, JsonValue]] = Field(default_factory=list)


class Mem0Event(BaseModel):
    """Single event from mem0 add/update operation."""

    id: str
    memory: str
    event: Literal["ADD", "UPDATE", "DELETE", "NOOP"]
    data: dict[str, str] = Field(default_factory=dict)


class Mem0AddResponse(BaseModel):
    """Response from mem0 add/update operation (v1.1+)."""

    results: list[Mem0Event] = Field(default_factory=list)


class Mem0UpdateResponse(BaseModel):
    """Response from mem0 update()."""

    message: str  # "Memory updated successfully"
    # Note: update() doesn't return results list


class AppConfig(BaseModel):
    """Represents a single application's configuration setup.

    This defines where an app's config files are, how they're structured,
    and what they depend on.

    Attributes:
        app_name: Name of the application (e.g., "zsh", "nvim", "alacritty")
        source_path: Location in dotfiles repo (e.g., "~/dotfiles/zsh/.zshrc")
        destination_path: Where config should be installed (e.g., "~/.zshrc")
        file_structure: Whether config is a single file or directory of modules
        dependencies: Other apps or configs this one requires

    """

    app_name: str
    source_path: str
    destination_path: str
    file_structure: Literal["modular", "monolithic"]
    dependencies: list[str | AppConfig] | None = None


class AppChange(AppConfig):
    """Represents a single modification to a dotfile configuration.

    Used by commit_contextual_change to log the semantic context of a change,
    not just the file diff. This creates a queryable history of "why" decisions
    were made.

    Attributes:
        app_name: Tool being modified (e.g., "zsh", "nvim", "alacritty")
        change_type: Category of change (e.g., "performance", "keybind", "plugin", "bugfix")
        rationale: Strategic reason for the change (the "why")
        improvement_metric: Quantifiable benefit (e.g., "startup -50ms", "reduced eye strain")
        description: Detailed explanation of what was changed (the "what")
        vcs_commit_id: Optional git/jj commit hash linking this change to VCS history

    """

    app_name: str
    change_type: str
    rationale: str
    improvement_metric: str
    description: str
    vcs_commit_id: str | None


class SystemMetadata(BaseModel):
    """Hardware and software environment details for a machine.

    This establishes the ground truth for a user's system, allowing the agent
    to make hardware-aware decisions (e.g., "Don't enable blur on low-end hardware").

    Attributes:
        os_version: Full OS details (e.g., "macOS 14.2", "Ubuntu 22.04 LTS")
        main_shell: Default shell
        main_terminal_emulator: Terminal app (e.g., "Alacritty", "Kitty", "iTerm2")
        main_prompt_engine: Prompt framework if any (e.g., "starship", "oh-my-zsh")
        main_editor: Primary text editor (e.g., "nvim", "vim", "emacs")
        version_control: Literal["git", "jj"]
        package_manager: str | None
        cpu: str
        extra: str

    """

    os_version: str
    main_shell: Literal[
        "Bash", "Zsh", "PowerShell", "Fish", "Sh", "Dash", "Ksh", "Tcsh", "Nushell"
    ]
    main_terminal_emulator: str
    main_prompt_engine: str | None
    main_editor: str
    version_control: Literal["git", "jj"]
    package_manager: str | None
    cpu: str
    extra: str


class HealthStatus(BaseModel):
    """Representation of the server's health status.

    Attributes:
        status: Overall status ("healthy" or "unhealthy")
        version: Current server version
        components: Status of individual components (memory, vcs, etc.)

    """

    status: str
    version: str
    components: dict[str, str]


class DriftResult(BaseModel):
    """Result of a configuration drift check."""

    status: Literal["clean", "modified", "error"]
    vcs_type: Literal["git", "jj"]
    modified_files: list[str]
    total_changes: int
    message: str
