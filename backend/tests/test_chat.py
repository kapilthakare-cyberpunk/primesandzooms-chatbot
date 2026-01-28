"""Tests for chat functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app


@pytest.fixture
def client():
    """Create test client with mocked vector store."""
    with patch('app.main.VectorStore') as mock_vs:
        mock_instance = Mock()
        mock_instance.similarity_search.return_value = []
        mock_instance.get_stats.return_value = {
            "total_documents": 0,
            "collection_name": "test",
            "embedding_model": "test"
        }
        mock_vs.return_value = mock_instance
        
        with TestClient(app) as client:
            yield client


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint_validation(client):
    """Test chat endpoint validates input."""
    # Empty message should fail
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_stats_endpoint(client):
    """Test stats endpoint returns data."""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    assert "total_documents" in response.json()


@pytest.mark.asyncio
async def test_rag_engine_query():
    """Test RAG engine query flow."""
    from app.services.rag_engine import RAGEngine
    from langchain.schema import Document
    
    # Mock vector store
    mock_vs = Mock()
    mock_vs.similarity_search.return_value = [
        Document(
            page_content="Test content about cameras",
            metadata={"source": "https://test.com"}
        )
    ]
    
    # Mock LLM client
    with patch('app.services.rag_engine.LLMClient') as mock_llm:
        mock_llm_instance = Mock()
        mock_llm_instance.chat = AsyncMock(return_value="Test response")
        mock_llm.return_value = mock_llm_instance
        
        engine = RAGEngine(mock_vs)
        result = await engine.query("What cameras do you have?")
        
        assert "response" in result
        assert "sources" in result
        assert result["response"] == "Test response"