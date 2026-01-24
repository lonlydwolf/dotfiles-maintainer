"""Tests for the MemoryManager core module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotfiles_maintainer.config import ServerConfig
from dotfiles_maintainer.core.memory import MemoryManager, MemorySearchError
from dotfiles_maintainer.core.types import (
    Mem0AddResponse,
    Mem0Event,
    Mem0UpdateResponse,
    MemoryResult,
    SearchResult,
)
from mem0 import AsyncMemory


@pytest.fixture
def mock_config() -> ServerConfig:
    """Fixture for mocking server configuration."""
    config = MagicMock(spec=ServerConfig)
    config.user_id = "test_user"
    # Ensure memory_config is also mocked or a valid object if needed
    config.memory_config = MagicMock()
    return config


@pytest.fixture
def mock_mem0_client() -> AsyncMock:
    """Fixture for mocking mem0 AsyncMemory client."""
    client = AsyncMock(spec=AsyncMemory)
    return client


@pytest.fixture
def memory_manager(
    mock_config: ServerConfig, mock_mem0_client: AsyncMock
) -> MemoryManager:
    """Fixture for creating MemoryManager with mocked dependencies."""
    with patch(
        "dotfiles_maintainer.core.memory.AsyncMemory", return_value=mock_mem0_client
    ):
        manager = MemoryManager(mock_config)
        # Ensure the client is indeed our mock (patch should handle this, but good to be sure)
        manager.client = mock_mem0_client
        return manager


@pytest.mark.asyncio
async def test_add_with_redaction_success(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test successful memory addition with redaction."""
    # Setup
    text = "secret key is sk-123456789012345678901234567890123456789012345678"
    expected_redacted = "secret key is [OPENAI_API_KEY_REDACTED]"

    mock_response = Mem0AddResponse(
        results=[Mem0Event(id="123", memory=expected_redacted, event="ADD")]
    )
    mock_mem0_client.add.return_value = mock_response

    # Execute
    result = await memory_manager.add_with_redaction(text)

    # Verify
    mock_mem0_client.add.assert_called_once_with(
        messages=expected_redacted, user_id="test_user", metadata=None
    )
    assert isinstance(result, Mem0AddResponse)
    assert result.results[0].id == "123"
    assert result.results[0].memory == expected_redacted


@pytest.mark.asyncio
async def test_search_success(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test successful search operation."""
    # Setup
    query = "test query"
    mock_results = SearchResult(
        results=[
            MemoryResult(
                id="1",
                memory="test memory",
                score=0.9,
                metadata={"type": "test"},
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            )
        ],
        relations=None,
    )
    mock_mem0_client.search.return_value = mock_results

    # Execute
    result = await memory_manager.search(query)

    # Verify
    mock_mem0_client.search.assert_called_once_with(
        query, user_id="test_user", limit=10
    )
    assert isinstance(result, SearchResult)
    assert result.results[0].id == "1"
    assert result.results[0].memory == "test memory"


@pytest.mark.asyncio
async def test_update_success(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test successful memory update."""
    # Setup
    memory_id = "123"
    text = "updated secret sk-123456789012345678901234567890123456789012345678"
    expected_redacted = "updated secret [OPENAI_API_KEY_REDACTED]"

    mock_response = Mem0UpdateResponse(
        id=memory_id,
        text=expected_redacted,
        updated_at="2023-01-01T00:00:00Z",
    )
    mock_mem0_client.update.return_value = mock_response

    # Execute
    result = await memory_manager.update(memory_id, text)

    # Verify
    mock_mem0_client.update.assert_called_once_with(
        data=expected_redacted, memory_id=memory_id
    )
    assert isinstance(result, Mem0UpdateResponse)
    assert result.id == memory_id
    assert result.text == expected_redacted


@pytest.mark.asyncio
async def test_add_with_redaction_failure(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test memory addition failure."""
    mock_mem0_client.add.side_effect = Exception("Add failed")
    with pytest.raises(Exception, match="Add failed"):
        await memory_manager.add_with_redaction("text")


@pytest.mark.asyncio
async def test_search_failure(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test search failure."""
    mock_mem0_client.search.side_effect = Exception("Search failed")
    with pytest.raises(MemorySearchError, match="Failed to search"):
        await memory_manager.search("query")


@pytest.mark.asyncio
async def test_search_empty_result(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test search with empty result."""
    mock_mem0_client.search.return_value = None
    result = await memory_manager.search("query")
    assert isinstance(result, SearchResult)
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_update_failure(
    memory_manager: MemoryManager, mock_mem0_client: AsyncMock
) -> None:
    """Test update failure."""
    mock_mem0_client.update.side_effect = Exception("Update failed")
    with pytest.raises(Exception, match="Update failed"):
        await memory_manager.update("123", "text")
