"""ChromaDB vector store wrapper."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings


class VectorStore:
    """Wrapper for ChromaDB vector operations."""
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding function
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Insert a list of LangChain Documents into the ChromaDB collection with embeddings and content-derived IDs.
        
        Each Document's page_content is embedded and stored as the document text, and its metadata is preserved. If `documents` is empty the method is a no-op. Generated entry IDs use the pattern `doc_<n>` where `<n>` is a deterministic integer derived from the document content (modulo 10**10).
         
        Parameters:
            documents (List[Document]): LangChain Document objects whose `page_content` will be embedded and uploaded; their `metadata` will be saved alongside each document.
        """
        if not documents:
            return
        
        # Extract texts and metadata
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings
        embeddings = self.embeddings.embed_documents(texts)
        
        # Generate IDs based on content hash
        ids = [f"doc_{hash(text) % 10**10}" for text in texts]
        
        # Upsert to ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Finds the top-k documents most similar to a query using the configured embeddings and collection.
        
        Generates an embedding for `query`, retrieves up to `k` nearest matches from the collection, and returns them as LangChain Document objects whose `metadata` contains the stored metadata plus a `distance` key when available.
        
        Parameters:
            query (str): The text query to search for.
            k (int): Maximum number of matching documents to return.
        
        Returns:
            List[Document]: List of matching LangChain Document objects with combined metadata and a `distance` entry when present.
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to LangChain Documents
        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                metadata["distance"] = results["distances"][0][i] if results["distances"] else None
                documents.append(Document(page_content=doc, metadata=metadata))
        
        return documents
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Provide basic statistics about the configured ChromaDB collection.
        
        Returns:
            stats (Dict[str, Any]): Dictionary with collection statistics:
                - total_documents (int): the collection's current document count.
                - collection_name (str): configured collection name.
                - embedding_model (str): configured embedding model name.
        """
        return {
            "total_documents": self.collection.count(),
            "collection_name": settings.COLLECTION_NAME,
            "embedding_model": settings.EMBEDDING_MODEL
        }
    
    def clear(self) -> None:
        """
        Remove all documents from the configured collection and reset it to an empty state.
        
        Deletes the collection identified by settings.COLLECTION_NAME and recreates it with HNSW cosine-space metadata so the collection is empty and ready for new inserts.
        """
        # Delete and recreate collection
        self.client.delete_collection(settings.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )