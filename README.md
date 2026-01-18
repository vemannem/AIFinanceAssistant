# AI Finance Assistant - Complete System

A production-ready AI-powered financial advisory system with RAG pipeline, multi-agent orchestration, and React TypeScript frontend.

## Quick Start

### Backend (Python/FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
# Server runs at http://localhost:8000
```

See [backend/README.md](backend/README.md) for details.

### Frontend (React/TypeScript)

```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:5173
```

See [frontend/README.md](frontend/README.md) for details.

### Run Both Together

```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## Project Structure

The project is organized as **two independent packages**:

- **`/backend`** - FastAPI server with RAG, multi-agent orchestration, guardrails
- **`/frontend`** - React 18 + TypeScript web interface

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete layout.

## Key Features

### Backend
- ✅ Vector DB Integration (Pinecone + OpenAI embeddings)
- ✅ RAG Pipeline (LLM-powered responses with citations)
- ✅ Multi-Agent Orchestration (6 specialized agents)
- ✅ Conversation Management (history + summaries)
- ✅ Safety Guardrails (9-layer protection)
- ✅ WebSocket Streaming (real-time responses)

### Frontend
- ✅ Chat Interface (message history, streaming)
- ✅ Portfolio Analysis (forms + visualizations)
- ✅ Responsive Design (mobile-first)
- ✅ Type-Safe (TypeScript + strict mode)
- ✅ State Management (Zustand)
- ✅ Configurable Backend URL (environment variables)

## Technology Stack

| Layer | Technology | Package Manager |
|-------|-----------|-----------------|
| **Backend** | Python 3.11, FastAPI, LangChain, Pinecone | pip (requirements.txt) |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS | npm (package.json) |
| **Database** | Pinecone (Vector), PostgreSQL (optional) | - |
| **LLM** | OpenAI GPT-4, embeddings-3-small | - |
| **Deployment** | Docker, Vercel, AWS | - |

## API Specification

Backend exposes REST + WebSocket APIs:

```
REST Endpoints:
  POST   /api/chat/finance-qa           # Send query
  GET    /api/chat/history/:sessionId   # Get conversation
  DELETE /api/chat/history/:sessionId   # Clear history
  GET    /api/chat/summary/:sessionId   # Get summary

WebSocket:
  WS     /ws/chat                       # Streaming responses
```

See [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) for full details.

## Configuration

### Backend
Configuration via `.env` file:
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=gcp-starter
```

### Frontend
Configuration via `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Development

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Run with auto-reload
python main.py
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run dev server (with hot reload)
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Deployment

### Deploy Backend
```bash
cd backend
docker build -t my-backend:latest .
docker push my-backend:latest
# Deploy to AWS ECS, Google Cloud Run, or similar
```

### Deploy Frontend
```bash
cd frontend
npm run build
# Deploy dist/ to Vercel, Netlify, or S3 + CloudFront
```

### Deploy Together (Docker Compose)
```bash
docker-compose up -d
```

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
pytest --cov=src tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## Documentation

- [Backend README](backend/README.md) - Backend setup & development
- [Frontend README](frontend/README.md) - Frontend setup & development
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed project layout
- [docs/BACKEND_HLD.md](docs/BACKEND_HLD.md) - Backend architecture with flow diagrams
- [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) - Complete API reference
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment guide
- [FRONTEND_DEV_LOG.md](FRONTEND_DEV_LOG.md) - Frontend development plan

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Backend Tests | 100% passing | ✅ 29/29 |
| API Latency | < 500ms | ✅ |
| Frontend Load | < 2s | ⏳ In development |
| Lighthouse Score | > 90 | ⏳ In development |
| Code Coverage | > 80% | ✅ Backend verified |
| Type Safety | 0 TypeScript errors | ✅ Frontend ready |

## Performance Targets

### Backend
- API response time: < 500ms
- Concurrent requests: 1000+
- Uptime: 99.9%

### Frontend
- First Contentful Paint: < 1.5s
- Lighthouse Score: > 90
- Bundle size: < 250KB (gzipped)

## Security

- ✅ Input validation (backend + frontend)
- ✅ Rate limiting on API endpoints
- ✅ CORS properly configured
- ✅ Environment variables for secrets
- ✅ SQL injection protection (ORM)
- ✅ XSS prevention (React escaping)
- ✅ HTTPS/TLS in production

## Architecture

```
User Browser
    ↓ HTTPS
Frontend (React/Vite)
    ↓ REST + WebSocket
Backend (FastAPI)
    ├─ RAG Pipeline → OpenAI GPT-4
    ├─ Multi-Agent Orchestration
    └─ Vector DB → Pinecone
```

See [docs/BACKEND_HLD.md](docs/BACKEND_HLD.md) for detailed architecture diagrams.

## Troubleshooting

### Backend Issues
- Backend won't start: Check `OPENAI_API_KEY` and `PINECONE_API_KEY`
- Port 8000 already in use: `lsof -i :8000` and kill the process
- See [backend/README.md](backend/README.md#troubleshooting)

### Frontend Issues
- Can't connect to backend: Check `VITE_API_URL` in `.env.local`
- Port 5173 already in use: `npm run dev -- --port 3000`
- See [frontend/README.md](frontend/README.md#troubleshooting)

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes to `/backend` or `/frontend` or both
3. Run tests: `pytest` (backend) or `npm test` (frontend)
4. Commit: `git commit -m "Add feature X"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

## License

MIT

## Support

- **Backend Issues**: See [backend/README.md](backend/README.md)
- **Frontend Issues**: See [frontend/README.md](frontend/README.md)
- **Architecture**: See [docs/BACKEND_HLD.md](docs/BACKEND_HLD.md)
- **API Reference**: See [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md)

---

## Project Status

**Backend**: ✅ Phase 1-2 Complete (100% - 29/29 tests passing)
**Frontend**: 🔄 Phase 3 In Development (Week 1 started)
**Overall**: ~90% Complete

**Target Launch**: February 1, 2026
