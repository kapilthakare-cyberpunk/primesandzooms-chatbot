"""Chat API endpoints."""

import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from app.services.rag_engine import RAGEngine

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    sources: List[str]
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """
    Handle a chat request by querying the RAG engine and returning the generated reply, sources, and session identifier.
    
    Parameters:
        chat_request (ChatRequest): Incoming chat payload. `message` is the user input to query. If `session_id` is not provided, a new UUID is generated and returned in the response.
    
    Returns:
        ChatResponse: The generated reply (`response`), a list of source identifiers (`sources`), and the `session_id` used for the conversation.
    
    Raises:
        HTTPException: With status code 500 if processing or the RAG query fails.
    """
    try:
        # Get or create session ID
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Get vector store from app state
        vector_store = request.app.state.vector_store
        
        # Initialize RAG engine and query
        rag_engine = RAGEngine(vector_store)
        result = await rag_engine.query(chat_request.message)
        
        return ChatResponse(
            response=result["response"],
            sources=result["sources"],
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Stream a chat response as Server-Sent Events (SSE) for the provided chat message.
    
    The response yields SSE `data:` events with JSON payloads:
    - Token events: `{"token": "<partial_text>"}` for incremental text chunks.
    - Done event: `{"done": true, "sources": ["source_id", ...]}` when the response is complete.
    - Error event: `{"error": "<error_message>"}` if an exception occurs during streaming.
    
    Returns:
        StreamingResponse: An SSE streaming response that emits the events described above with media type "text/event-stream" and headers to disable caching and keep the connection alive.
    """
    import json
    
    async def generate():
        """
        Yield Server-Sent Event (SSE) formatted strings streaming token and completion events from the RAG engine.
        
        This async generator retrieves the application's vector store, runs a streaming query for the incoming message, and yields SSE "data" lines containing JSON payloads for each chunk. It emits token chunks as {"token": string}, a final completion chunk as {"done": true, "sources": [..]}, and on error emits {"error": string}.
        
        Returns:
            An async iterator that yields SSE data event strings (each includes a trailing blank line), where each yielded string contains a JSON payload for a token, a done event with sources, or an error message.
        """
        try:
            vector_store = request.app.state.vector_store
            rag_engine = RAGEngine(vector_store)
            
            async for chunk in rag_engine.query_stream(chat_request.message):
                if chunk["type"] == "token":
                    yield f"data: {json.dumps({'token': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    yield f"data: {json.dumps({'done': True, 'sources': chunk['sources']})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )