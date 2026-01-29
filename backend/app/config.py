"""Application configuration using Pydantic settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Primes and Zooms Rental Chatbot"
    debug: bool = False
    
    # API Keys
    openai_api_key: str = ""
    groq_api_key: str = ""  # Optional, for Groq LLM
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""  # Optional, for Telegram integration
    TELEGRAM_WEBHOOK_SECRET: str = ""  # Optional, for webhook verification
    
    # LLM Configuration
    llm_provider: str = "openai"  # openai, groq
    llm_model: str = "gpt-4o-mini"  # Default model
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    
    # Vector Store (ChromaDB)
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "rental_docs"
    
    # RAG Configuration
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Website Scraping
    target_website: str = "https://www.primesandzooms.com"
    max_pages_to_crawl: int = 50
    crawl_delay_seconds: float = 1.0
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
