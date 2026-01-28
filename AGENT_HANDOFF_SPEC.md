# AI Agent Handoff Specification
## Primes and Zooms RAG Chatbot

> **Purpose**: This document provides complete context for AI coding agents to understand, modify, and extend this codebase.

---

## 1. PROJECT OVERVIEW

### 1.1 Business Context
- **Client**: Primes and Zooms - Photography & video equipment rental business in Pune, India
- **Website**: www.primesandzooms.com
- **Goal**: Customer service chatbot to answer questions about rentals, equipment, pricing, and processes
- **Budget**: Minimal (< $5 for demo)

### 1.2 Technical Summary
```
Architecture: RAG (Retrieval-Augmented Generation)
Backend: FastAPI + Python 3.11+
Vector DB: ChromaDB (local, persistent)
LLM: OpenAI GPT-4o-mini
Embeddings: OpenAI text-embedding-3-small
Orchestration: LangChain
```

### 1.3 Repository Structure
```
primesandzooms-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings management
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # POST /chat, /chat/stream
│   │   │   └── admin.py         # POST /admin/ingest, GET /admin/stats
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rag_engine.py    # Core RAG orchestration
│   │   │   ├── vector_store.py  # ChromaDB operations
│   │   │   └── llm_client.py    # OpenAI abstraction
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py       # Website content extraction
│   │   │   └── chunker.py       # Text chunking logic
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── templates.py     # System prompts
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py       # Pydantic models
│   ├── data/
│   │   └── chroma_db/           # Vector store (gitignored)
│   ├── tests/
│   │   └── test_chat.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── README.md
└── AGENT_HANDOFF_SPEC.md        # This file
```

---

## 2. CORE COMPONENTS

### 2.1 FastAPI Application (`main.py`)
```python
# Entry point - includes CORS, routers, health check
# Mounts: /chat, /admin routes
# Startup: Initializes vector store connection
```

### 2.2 RAG Engine (`services/rag_engine.py`)
**Purpose**: Orchestrates the retrieve-then-generate flow

**Key Functions**:
- `query(user_message: str) -> str` - Main entry point
- `_retrieve(query: str, k: int) -> List[Document]` - Vector search
- `_generate(query: str, context: List[Document]) -> str` - LLM call

**Flow**:
```
User Query → Embed Query → Vector Search (top-k) → Build Prompt → LLM → Response
```

### 2.3 Vector Store (`services/vector_store.py`)
**Purpose**: ChromaDB wrapper for document storage/retrieval

**Key Functions**:
- `add_documents(docs: List[Document])` - Upsert with embeddings
- `similarity_search(query: str, k: int) -> List[Document]`
- `get_stats() -> dict` - Collection metrics

**Config**:
```python
COLLECTION_NAME = "primesandzooms_docs"
PERSIST_DIR = "./data/chroma_db"
EMBEDDING_MODEL = "text-embedding-3-small"
```

### 2.4 LLM Client (`services/llm_client.py`)
**Purpose**: OpenAI API abstraction

**Key Functions**:
- `chat(messages: List[dict]) -> str` - Completion call
- `chat_stream(messages: List[dict]) -> Generator` - Streaming
- `embed(text: str) -> List[float]` - Single embedding
- `embed_batch(texts: List[str]) -> List[List[float]]` - Batch

**Config**:
```python
MODEL = "gpt-4o-mini"  # Cost-effective
TEMPERATURE = 0.3      # Factual responses
MAX_TOKENS = 500       # Concise answers
```

### 2.5 Ingestion Pipeline (`ingestion/`)
**scraper.py**:
- Fetches pages from primesandzooms.com
- Extracts text content (BeautifulSoup)
- Handles equipment pages, pricing, FAQ, terms

**chunker.py**:
- Splits content into ~500 token chunks
- 50 token overlap for context continuity
- Preserves metadata (source URL, title)

---

## 3. API SPECIFICATION

### 3.1 Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
  "message": "What cameras do you have for rent?",
  "session_id": "optional-session-id"
}

Response 200:
{
  "response": "We have several cameras available...",
  "sources": ["https://primesandzooms.com/equipment"],
  "session_id": "uuid"
}
```

### 3.2 Streaming Chat
```http
POST /chat/stream
Content-Type: application/json

{
  "message": "Tell me about your rental process"
}

Response: Server-Sent Events (SSE)
data: {"token": "We"}
data: {"token": " have"}
data: {"token": " a"}
...
data: {"done": true, "sources": [...]}
```

### 3.3 Admin - Ingest Content
```http
POST /admin/ingest
Content-Type: application/json

{
  "urls": ["https://primesandzooms.com"],
  "crawl_depth": 2
}

Response 200:
{
  "status": "success",
  "documents_ingested": 45,
  "chunks_created": 128
}
```

### 3.4 Admin - Stats
```http
GET /admin/stats

Response 200:
{
  "total_documents": 128,
  "collection_name": "primesandzooms_docs",
  "embedding_model": "text-embedding-3-small"
}
```

---

## 4. CONFIGURATION

### 4.1 Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
CHROMA_PERSIST_DIR=./data/chroma_db
COLLECTION_NAME=primesandzooms_docs
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
RETRIEVAL_TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### 4.2 Dependencies (`requirements.txt`)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
openai==1.12.0
chromadb==0.4.22
langchain==0.1.6
langchain-openai==0.0.5
langchain-community==0.0.17
beautifulsoup4==4.12.3
requests==2.31.0
pydantic==2.6.0
sse-starlette==1.8.2
```

---

## 5. COMMON AGENT TASKS

### Task: Add new content source
```python
# In ingestion/scraper.py, add to SEED_URLS:
SEED_URLS = [
    "https://primesandzooms.com",
    "https://primesandzooms.com/new-page",  # Add here
]
```

### Task: Modify system prompt
```python
# In prompts/templates.py, edit SYSTEM_PROMPT
```

### Task: Adjust retrieval parameters
```python
# In config.py or .env:
RETRIEVAL_TOP_K=10  # More context
CHUNK_SIZE=300      # Smaller chunks
```

### Task: Add conversation memory
```python
# In services/rag_engine.py:
# 1. Add session storage (Redis or in-memory dict)
# 2. Prepend conversation history to prompt
# 3. Limit to last N turns to manage tokens
```

### Task: Deploy to production
```bash
# Using Docker:
cd backend
docker build -t pz-chatbot .
docker run -p 8000:8000 --env-file .env pz-chatbot

# Or Railway/Render:
# Point to backend/ directory, set OPENAI_API_KEY
```

---

## 6. TESTING

### 6.1 Quick Test Commands
```bash
# Start server
cd backend
uvicorn app.main:app --reload

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What cameras do you rent?"}'

# Test ingestion
curl -X POST http://localhost:8000/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://primesandzooms.com"]}'

# Check stats
curl http://localhost:8000/admin/stats
```

### 6.2 Pytest
```bash
cd backend
pytest tests/ -v
```

---

## 7. COST ESTIMATION

| Component | Cost |
|-----------|------|
| ChromaDB | Free (local) |
| GPT-4o-mini | ~$0.15/1M input, $0.60/1M output |
| text-embedding-3-small | $0.02/1M tokens |
| **Demo (1000 queries)** | **~$2-3** |

---

## 8. KNOWN LIMITATIONS

1. **No auth** - Admin endpoints unprotected (add API key for prod)
2. **No conversation memory** - Each query is independent
3. **Single collection** - All docs in one ChromaDB collection
4. **No rate limiting** - Add for production use

---

## 9. EXTENSION IDEAS

- [ ] Add WhatsApp integration (Twilio)
- [ ] Implement booking creation via chat
- [ ] Add analytics dashboard
- [ ] Multi-language support (Hindi)
- [ ] Voice input/output

---

*Last updated: 2025-01-29*
*Handoff format version: 1.0*