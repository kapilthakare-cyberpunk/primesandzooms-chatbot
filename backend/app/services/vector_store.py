"""ChromaDB vector store operations."""
import logging
from datetime import datetime
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import Settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector store operations using ChromaDB."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        
        # Initialize ChromaDB client with persistence
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Initialize LangChain Chroma wrapper
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
        )
        
        logger.info(f"Vector store initialized at {settings.chroma_persist_dir}")
    
    async def add_documents(self, documents: list[Document]) -> int:
        """Add documents to the vector store.
        
        Args:
            documents: List of LangChain Document objects with metadata
            
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        # Add ingestion timestamp to all documents
        timestamp = datetime.utcnow().isoformat()
        for doc in documents:
            doc.metadata["ingestion_timestamp"] = timestamp
        
        # Add to vector store
        self.vectorstore.add_documents(documents)
        
        logger.info(f"Added {len(documents)} documents to vector store")
        return len(documents)
    
    async def similarity_search(
        self,
        query: str,
        top_k: int | None = None,
        filter_dict: dict | None = None
    ) -> list[Document]:
        """Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        k = top_k or self.settings.top_k_results
        
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter=filter_dict,
        )
        
        # Filter by similarity threshold
        filtered_results = [
            doc for doc, score in results 
            if score >= self.settings.similarity_threshold
        ]
        
        logger.info(
            f"Query returned {len(results)} results, "
            f"{len(filtered_results)} above threshold"
        )
        
        return filtered_results
    
    async def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        collection = self.chroma_client.get_collection(
            name=self.settings.chroma_collection_name
        )
        
        count = collection.count()
        
        # Get unique source URLs
        all_metadata = collection.get(include=["metadatas"])
        source_urls = set()
        latest_timestamp = None
        
        if all_metadata and all_metadata.get("metadatas"):
            for meta in all_metadata["metadatas"]:
                if meta.get("source_url"):
                    source_urls.add(meta["source_url"])
                if meta.get("ingestion_timestamp"):
                    ts = meta["ingestion_timestamp"]
                    if not latest_timestamp or ts > latest_timestamp:
                        latest_timestamp = ts
        
        return {
            "total_chunks": count,
            "total_pages": len(source_urls),
            "last_ingestion": latest_timestamp,
            "collection_name": self.settings.chroma_collection_name,
        }
    
    async def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.chroma_client.delete_collection(
                name=self.settings.chroma_collection_name
            )
            # Recreate empty collection
            self.vectorstore = Chroma(
                client=self.chroma_client,
                collection_name=self.settings.chroma_collection_name,
                embedding_function=self.embeddings,
            )
            logger.info("Collection cleared and recreated")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
