"""Memory management with centralized error handling."""

import logging

from mem0 import AsyncMemory
from pydantic import ValidationError

from ..config import ServerConfig
from ..utils.secrets import redact_secrets
from .types import Mem0AddResponse, Mem0UpdateResponse, SearchResult

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
