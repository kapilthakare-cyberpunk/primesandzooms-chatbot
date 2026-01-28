"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, admin
from app.services.vector_store import VectorStore
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize vector store
    app.state.vector_store = VectorStore()
    print(f"✅ Vector store initialized: {settings.COLLECTION_NAME}")
    yield
    # Shutdown: Cleanup if needed
    print("👋 Shutting down...")


app = FastAPI(
    title="Primes and Zooms Chatbot",
    description="RAG-powered customer service chatbot for photography equipment rental",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, tags=["Chat"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "primes-and-zooms-chatbot"}