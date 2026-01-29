"""RAG (Retrieval-Augmented Generation) engine."""

from typing import Dict, Any, AsyncGenerator

from app.services.vector_store import VectorStore
from app.services.llm_client import LLMClient
from app.prompts.templates import SYSTEM_PROMPT, build_context_prompt
from app.config import get_settings


class RAGEngine:
    """Orchestrates the RAG pipeline: retrieve relevant docs, then generate response."""
    
    def __init__(self, vector_store: VectorStore):
        """Initialize RAG engine with vector store."""
        self.vector_store = vector_store
        self.llm_client = LLMClient()
        self.settings = get_settings()
    
    async def query(self, user_message: str) -> Dict[str, Any]:
        """Process a user query through the RAG pipeline.
        
        Args:
            user_message: The user's question or message
            
        Returns:
            Dict containing 'response' and 'sources'
        """
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.vector_store.similarity_search(
            query=user_message,
            top_k=self.settings.top_k_results
        )
        
        # Step 2: Build context from retrieved documents
        context = build_context_prompt(retrieved_docs)
        sources = list(set(doc.metadata.get("source", "") for doc in retrieved_docs if doc.metadata.get("source")))
        
        # Step 3: Generate response using LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_message}"}
        ]
        
        response = await self.llm_client.chat(messages)
        
        return {
            "response": response,
            "sources": sources
        }
    
    async def query_stream(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user query and stream the response.
        
        Args:
            user_message: The user's question or message
            
        Yields:
            Dict with 'type' ('token' or 'done') and content
        """
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.vector_store.similarity_search(
            query=user_message,
            top_k=self.settings.top_k_results
        )
        
        # Step 2: Build context from retrieved documents
        context = build_context_prompt(retrieved_docs)
        sources = list(set(doc.metadata.get("source", "") for doc in retrieved_docs if doc.metadata.get("source")))
        
        # Step 3: Stream response from LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_message}"}
        ]
        
        async for token in self.llm_client.chat_stream(messages):
            yield {"type": "token", "content": token}
        
        yield {"type": "done", "sources": sources}
