"""Memory management with centralized error handling."""

import logging
import shutil

from mem0 import AsyncMemory
from pydantic import ValidationError

from ..config import ServerConfig
from ..utils.secrets import redact_secrets
from .types import (
    Mem0AddResponse,
    Mem0DeleteResponse,
    Mem0GetAllResponse,
    Mem0UpdateResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


class MemorySearchError(Exception):
    """Raised when memory search fails."""

    pass


class MemoryManager:
    """High-level interface for semantic memory operations.

    Handles configuration, redaction, and error logging.
    """

    def __init__(self, config: ServerConfig):
        """Initialize the memory manager with a specific configuration."""
        self.config: ServerConfig = config
        self.user_id: str = config.user_id

        # Initialize the AsyncMemory client
        self.client: AsyncMemory = AsyncMemory(config=config.memory_config)

    async def add_with_redaction(
        self, text: str, metadata: dict[str, str | bool] | None = None
    ) -> Mem0AddResponse:
        """Add memory with automatic secret redaction.

        Returns:
            Mem0AddResponse with results list containing ADD/UPDATE/DELETE events.

        Raises:
            ValidationError: if mem0 returns unexpected structure.
        """
        try:
            result = await self.client.add(
                messages=redact_secrets(text),
                user_id=self.user_id,
                metadata=metadata,
            )

            return Mem0AddResponse.model_validate(result)

        except ValidationError as e:
            logger.error(f"Invalid mem0 add response: {e}")
            return Mem0AddResponse(results=[])
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise

    async def search(self, query: str, limit: int = 10) -> SearchResult:
        """Perform a semantic search in the vector store with error handling.

        Args:
            query (str): The semantic search query string.
            limit (int): Maximum number of results to return (default: 10).

        Returns:
            SearchResult containing matching memories ordered by relevance.

        Raises:
            MemorySearchError: If the search operation fails.

        """
        try:
            result = await self.client.search(query, user_id=self.user_id, limit=limit)
            if not result:
                return SearchResult(results=[], relations=None)

            return SearchResult.model_validate(result)

        except ValidationError as e:
            logger.error(f"Invalid search result structure: {e}")
            return SearchResult(results=[], relations=None)
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise MemorySearchError(f"Failed to search: {e}") from e

    async def update(self, memory_id: str, text: str) -> Mem0UpdateResponse:
        """Update an existing memory entry.

        Returns:
            Mem0UpdateResponse with success message.
        """
        try:
            result = await self.client.update(
                data=redact_secrets(text),
                memory_id=memory_id,
            )
            return Mem0UpdateResponse.model_validate(result)
        except ValidationError as e:
            logger.error(f"Invalid update response: {e}")
            raise
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            raise

    async def get_all(self, limit: int = 100) -> Mem0GetAllResponse:
        """Retrieve all memories from the store.

        Args:
            limit (int): Maximum number of memories to retrieve.

        Returns:
            SearchResult with all memories.
        """
        try:
            # Note: AsyncMemory.get_all might differ slightly based on version.
            # We assume it supports user_id filtering.
            result = await self.client.get_all(user_id=self.user_id, limit=limit)
            return Mem0GetAllResponse.model_validate(result)

        except Exception as e:
            logger.error(f"Failed to retrieve all memories: {e}")
            raise

    async def delete_all(self) -> Mem0DeleteResponse:
        """Delete all memories for the current user."""

        try:
            result = await self.client.delete_all(user_id=self.user_id)
            return Mem0DeleteResponse.model_validate(result)

        except Exception as e:
            logger.error(f"Failed to reset memory: {e}")
            raise

    async def reset(self) -> None:
        """Delete all memories for all users"""

        try:
            await self.client.reset()
            # Force cleanup of local Qdrant storage if it exists to prevent ghost duplicates
            if self.config.memory_db_path.exists():
                logger.info(
                    f"Removing persistent storage at {self.config.memory_db_path}"
                )
                shutil.rmtree(self.config.memory_db_path)
                self.config.memory_db_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to reset memory: {e}")
            raise
