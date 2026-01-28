# Primes and Zooms RAG Chatbot

AI-powered customer service chatbot for [Primes and Zooms](https://primesandzooms.com) - Photography & video equipment rental in Pune, India.

## 🎯 Features

- Answer questions about equipment, pricing, and rental process
- RAG-powered responses grounded in actual website content
- Streaming responses for better UX
- Admin endpoints for content ingestion

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Vector DB**: ChromaDB (local, free)
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: text-embedding-3-small
- **Orchestration**: LangChain

## 🚀 Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/kapilthakare-cyberpunk/primesandzooms-chatbot.git
cd primesandzooms-chatbot/backend
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

### 5. Ingest website content

```bash
curl -X POST http://localhost:8000/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://primesandzooms.com"]}'
```

### 6. Test the chatbot

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What cameras do you have for rent?"}'
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Settings
│   ├── routes/           # API endpoints
│   ├── services/         # RAG, Vector store, LLM
│   ├── ingestion/        # Scraping & chunking
│   └── prompts/          # System prompts
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send a message, get a response |
| POST | `/chat/stream` | Streaming response (SSE) |
| POST | `/admin/ingest` | Ingest website content |
| GET | `/admin/stats` | Vector store statistics |
| GET | `/health` | Health check |

## 💰 Cost

Estimated **< $5** for demo usage (1000+ queries)

## 📄 Documentation

See [AGENT_HANDOFF_SPEC.md](./AGENT_HANDOFF_SPEC.md) for detailed technical documentation.

## 📝 License

MIT