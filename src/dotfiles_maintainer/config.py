"""Server configuration with validation."""

import logging
import os
from pathlib import Path
from typing import ClassVar, Literal

from langchain_huggingface import HuggingFaceEmbeddings
from mem0.configs.base import MemoryConfig
from mem0.embeddings.configs import EmbedderConfig
from mem0.llms.configs import LlmConfig
from mem0.vector_stores.configs import VectorStoreConfig
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai", "anthropic", "gemini", "ollama"]


class ServerConfig(BaseSettings):
    """Validated server configuration.

    Loads from environment variables with DOTFILES_ prefix.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="DOTFILES_", case_sensitive=False
    )

    # User settings (Loads from DOTFILES_USER_ID)
    user_id: str = Field(
        default_factory=lambda: os.getenv("USER", "default_user"),
        min_length=1,
        max_length=50,
        description="The user ID used for memory partitioning",
    )

    # Storage (Loads from DOTFILES_MEMORY_PATH)
    memory_db_path: Path = Field(
        default=Path("~/.dotfiles-mcp/qdrant"),
        validation_alias="DOTFILES_MEMORY_PATH",
        description="Qdrant database path",
    )

    # Internal LLM settings
    llm_provider: LLMProvider = Field(
        default="gemini",
        description="Which LLM provider to use for internal memory operations.",
    )
    llm_model: str = Field(
        default="gemini-3-flash-preview",
        validation_alias="LLM_MODEL",
        description="Specific model name (e.g. gpt-4o, gemini-3-flash-preview)",
    )
    llm_key: str = Field(
        default="", description="The LLM API key or base_url for ollama"
    )

    @computed_field
    @property
    def llm_config(self) -> LlmConfig:
        """Constructs the LLm configuration based on the provider.

        Requires appropriate API keys to be set in the environment.
        """
        # OLLAMA does not need an API key usually but needs a base_url
        if self.llm_provider == "ollama":
            return LlmConfig(
                provider="ollama",
                config={"model": self.llm_model, "base_url": self.llm_key},
            )
        if not self.llm_key:
            logger.warning(
                f"No API key found for {self.llm_provider}. Memory operations may fail."
            )

        return LlmConfig(
            provider=self.llm_provider,
            config={
                "model": self.llm_model,
                "api_key": self.llm_key,
            },
        )

    # Embeddings
    @computed_field
    @property
    def embedding_model(self) -> str:
        """Return the name of the sentence-transformer model."""
        return "all-MiniLM-L6-v2"

    @computed_field
    @property
    def embedding_dims(self) -> int:
        """Return the embedding dimension count (e.g., 384)."""
        return 384

    @computed_field
    @property
    def embedder_model(self) -> HuggingFaceEmbeddings:
        """Initialize the HuggingFace embedding engine."""
        return HuggingFaceEmbeddings(model_name=self.embedding_model)

    @computed_field
    @property
    def memory_config(self) -> MemoryConfig:
        """Construct the full mem0 configuration object."""
        return MemoryConfig(
            version="v1.1",  # This controls output format globally
            vector_store=VectorStoreConfig(
                provider="qdrant",
                config={
                    "path": str(self.memory_db_path),
                    "on_disk": True,
                    "embedding_model_dims": self.embedding_dims,
                },
            ),
            llm=self.llm_config,
            embedder=EmbedderConfig(
                provider="langchain",
                config={
                    "model": self.embedder_model,
                },
            ),
        )

    # Loggings
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
        description="Log level [NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL]",
    )

    # Features
    enable_backup: bool = Field(default=True, description="Backup toggle")
    enable_secrets_scan: bool = Field(default=True, description="Secrets Scan Toggle")

    vcs_timeout: int = Field(
        default=10,
        ge=1,
        le=300,
        validation_alias="DOTFILES_VCS_TIMEOUT",
        description="VCS command timeout in seconds",
    )

    @field_validator("memory_db_path", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand ~ and ensure parent directory exists."""
        path = Path(v).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
