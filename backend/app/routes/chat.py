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
    """Process a chat message and return a response."""
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
    """Process a chat message and stream the response."""
    import json
    
    async def generate():
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