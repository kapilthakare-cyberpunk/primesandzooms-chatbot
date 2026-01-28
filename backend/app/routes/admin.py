"""Admin API endpoints for content management."""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from app.ingestion.scraper import WebScraper
from app.ingestion.chunker import TextChunker

router = APIRouter()


class IngestRequest(BaseModel):
    """Content ingestion request."""
    urls: List[str]
    crawl_depth: Optional[int] = 1


class IngestResponse(BaseModel):
    """Content ingestion response."""
    status: str
    documents_ingested: int
    chunks_created: int


class StatsResponse(BaseModel):
    """Vector store statistics response."""
    total_documents: int
    collection_name: str
    embedding_model: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: Request, ingest_request: IngestRequest):
    """Ingest content from URLs into the vector store."""
    try:
        vector_store = request.app.state.vector_store
        
        # Scrape content from URLs
        scraper = WebScraper()
        documents = await scraper.scrape_urls(
            ingest_request.urls, 
            depth=ingest_request.crawl_depth
        )
        
        # Chunk the documents
        chunker = TextChunker()
        chunks = chunker.chunk_documents(documents)
        
        # Add to vector store
        vector_store.add_documents(chunks)
        
        return IngestResponse(
            status="success",
            documents_ingested=len(documents),
            chunks_created=len(chunks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request):
    """Get vector store statistics."""
    try:
        vector_store = request.app.state.vector_store
        stats = vector_store.get_stats()
        
        return StatsResponse(
            total_documents=stats["total_documents"],
            collection_name=stats["collection_name"],
            embedding_model=stats["embedding_model"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))