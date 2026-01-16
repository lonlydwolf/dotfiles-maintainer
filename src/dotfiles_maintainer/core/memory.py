"""Memory management with centralized error handling."""

import logging
from typing import cast

from mem0 import AsyncMemory

from ..config import ServerConfig
from ..utils.secrets import redact_secrets
from .types import JSONValue, Mem0Event, Mem0Response, MemoryResult, SearchResult

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

    def _validate_search_result(self, result: object) -> SearchResult:
        """Validate and convert mem0 response to SearchResult."""
        if not isinstance(result, dict):
            # Mem0 might return a list directly in some versions
            if isinstance(result, list):
                # Validate that each item in the list can be treated as a MemoryResult
                results: list[MemoryResult] = []
                for item in result:
                    if isinstance(item, dict) and "id" in item and "memory" in item:
                        # Ensure compatibility with MemoryResult
                        item_obj = cast(object, item)
                        results.append(cast(MemoryResult, item_obj))
                return {"results": results, "relations": None}
            raise TypeError(f"Expected dict or list, got {type(result)}")

        # If it is a dict, check for 'results' key
        raw_results = result.get("results")
        results_list: list[MemoryResult] = []
        if isinstance(raw_results, list):
            for item in raw_results:
                if isinstance(item, dict) and "id" in item and "memory" in item:
                    item_obj = cast(object, item)
                    results_list.append(cast(MemoryResult, item_obj))

        validated: SearchResult = {
            "results": results_list,
            "relations": cast(list[JSONValue] | None, result.get("relations")),
        }
        return validated

    async def add_with_redaction(
        self, text: str, metadata: dict[str, str | bool] | None = None
    ) -> list[Mem0Event] | Mem0Response:
        """Add memory with automatic secret redaction."""
        try:
            result = await self.client.add(
                redact_secrets(text), user_id=self.user_id, metadata=metadata
            )
            # Safe cast assuming mem0 returns list of events or response dict
            return cast(list[Mem0Event] | Mem0Response, cast(object, result))
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise

    async def search(self, query: str, limit: int = 10) -> SearchResult:
        """Perform a semantic search in the vector store with error handling.

        Args:
            query (str): The semantic search query string.
            limit (int): Maximum number of results to return (default: 10).

        Returns:
            SearchResult: A dict containing results and relations.

        Raises:
            MemorySearchError: If the search operation fails.

        """
        try:
            result = await self.client.search(query, user_id=self.user_id, limit=limit)
            if not result:
                return {"results": [], "relations": None}
            return self._validate_search_result(result)
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise MemorySearchError(f"Failed to search: {e}") from e

    async def update(self, memory_id: str, text: str) -> Mem0Response:
        """Update an existing memory entry."""
        try:
            result = await self.client.update(
                data=redact_secrets(text),
                memory_id=memory_id,
            )
            return cast(Mem0Response, cast(object, result))
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            raise
