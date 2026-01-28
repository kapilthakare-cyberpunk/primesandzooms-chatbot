"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Chat models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What cameras do you have for rent?",
                "session_id": "abc123"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant's response")
    sources: List[str] = Field(default_factory=list, description="Source URLs used")
    session_id: str = Field(..., description="Session ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "We have several cameras available including...",
                "sources": ["https://primesandzooms.com/equipment"],
                "session_id": "abc123"
            }
        }


# Admin models
class IngestRequest(BaseModel):
    """Request model for content ingestion."""
    urls: List[str] = Field(..., min_length=1, description="URLs to scrape")
    crawl_depth: int = Field(default=1, ge=1, le=3, description="Crawl depth (1-3)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "urls": ["https://primesandzooms.com"],
                "crawl_depth": 2
            }
        }


class IngestResponse(BaseModel):
    """Response model for content ingestion."""
    status: str
    documents_ingested: int
    chunks_created: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    """Response model for vector store statistics."""
    total_documents: int
    collection_name: str
    embedding_model: str


# Document models for internal use
class DocumentChunk(BaseModel):
    """Represents a chunk of content for embedding."""
    content: str
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class RetrievedDocument(BaseModel):
    """Represents a document retrieved from vector store."""
    content: str
    source: str
    title: Optional[str] = None
    relevance_score: float = 0.0