# Quick Start - AI Finance Assistant Backend

## Setup (One-time)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` in project root:
```env
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
PINECONE_API_KEY=pcsk_YOUR_KEY_HERE
PINECONE_INDEX_NAME=ai-finance-knowledge-base
```

### 3. Verify Configuration
```bash
python3 -c "from src.core.config import Config; Config.validate(); print('✅ Config OK')"
```

---

## Running the Server

### Start FastAPI Server
```bash
python3 -m uvicorn src.web_app:app --host 0.0.0.0 --port 8000 --reload
```

Then visit: **http://localhost:8000/docs** (Swagger UI)

### Test the Backend
```bash
python3 test_backend.py
```

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```
Response:
```json
{"status": "ok", "version": "0.1.0"}
```

### Finance Q&A Chat
```bash
curl -X POST http://localhost:8000/api/chat/finance-qa \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is diversification?"
  }'
```

**Response Example:**
```json
{
  "session_id": "abc123...",
  "message": "Diversification is the investment strategy of spreading your investments across different asset classes...",
  "citations": [
    {
      "title": "What Is Diversification?",
      "source_url": "https://www.investopedia.com/...",
      "category": "portfolio_management"
    }
  ],
  "timestamp": "2026-01-14T06:00:00.000Z",
  "metadata": {
    "agent": "finance_qa",
    "tools_used": ["pinecone_retrieval", "openai_chat"],
    "chunks_retrieved": 1
  }
}
```

### With Category Filter
```bash
curl -X POST http://localhost:8000/api/chat/finance-qa \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about ETFs",
    "category_filter": "etfs"
  }'
```

### With Conversation History
```bash
curl -X POST http://localhost:8000/api/chat/finance-qa \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How should I rebalance?",
    "session_id": "user-123",
    "conversation_history": [
      {"role": "user", "content": "I have 60% stocks, 40% bonds"},
      {"role": "assistant", "content": "That's a moderate allocation..."}
    ]
  }'
```

---

## Endpoints

| Method | Path | Description |
|--------|------|---|
| GET | `/health` | Health check |
| GET | `/config` | Show configuration |
| POST | `/api/chat/finance-qa` | Finance Q&A with RAG |

---

## Monitoring

### View Logs
Logs are printed as JSON. Filter specific agent:
```bash
python3 test_backend.py 2>&1 | grep '"logger": "agent.finance_qa"'
```

### Check Pinecone Index
```bash
python3 << 'EOF'
from src.rag import get_rag_retriever
retriever = get_rag_retriever()
results = retriever.index.describe_index_stats()
print(f"Vectors in index: {results['total_vector_count']}")
print(f"Dimensions: {results['dimension']}")
EOF
```

---

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
# Make sure .env exists and has the key
cat .env | grep OPENAI_API_KEY

# Or set via environment
export OPENAI_API_KEY="sk-..."
python3 -m uvicorn src.web_app:app --host 0.0.0.0 --port 8000
```

### "Cannot connect to Pinecone"
```bash
# Verify API key is correct
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('PINECONE_API_KEY')[:10])"

# Check Pinecone index status
python3 << 'EOF'
from src.rag import get_rag_retriever
r = get_rag_retriever()
print(r.index.describe_index_stats())
EOF
```

### RAG returns 0 chunks
This is normal if relevance score is below threshold (0.50 by default). The agent will still answer using the LLM's knowledge.

To see scores:
```bash
python3 test_backend.py 2>&1 | grep "Match score"
```

---

## Development

### Add New Agent
1. Create `src/agents/YOUR_AGENT.py`
2. Extend `BaseAgent` class
3. Implement `async def execute()`
4. Add route in `src/web_app/routes/YOUR_AGENT.py`

### Add New Endpoint
1. Create file in `src/web_app/routes/`
2. Define FastAPI router with `@router.post()`
3. Import in `src/web_app/__init__.py`
4. Add to app: `app.include_router(router, prefix="/api")`

---

## Architecture

```
Client
  ↓
FastAPI (uvicorn)
  ├─ /health → OK
  ├─ /config → Settings
  └─ /api/chat/finance-qa → FinanceQAAgent
        ├─ RAGRetriever → Pinecone
        └─ LLMProvider → OpenAI
```

---

**Ready to go!** 🚀

For more info, see `BACKEND_DEV_LOG.md`
