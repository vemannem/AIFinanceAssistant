# AI Finance Assistant - Project Structure

This project consists of **two independent packages**: Backend (FastAPI) and Frontend (React/TypeScript).

## Directory Layout

```
AIFinanceAssistent/
├── backend/                          # FastAPI backend (Python)
│   ├── src/
│   │   ├── core/                    # Core modules (RAG, embeddings)
│   │   ├── orchestration/           # Multi-agent orchestration
│   │   ├── agents/                  # Individual agent implementations
│   │   ├── guardrails/              # Safety guardrails
│   │   ├── database/                # Database models & operations
│   │   └── api/                     # FastAPI endpoints
│   ├── tests/                       # Backend tests
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Backend env configuration
│   ├── main.py                      # FastAPI app entry point
│   ├── README.md                    # Backend documentation
│   └── Dockerfile                   # Backend containerization
│
├── frontend/                        # React/TypeScript frontend
│   ├── src/
│   │   ├── config/                 # Configuration management
│   │   ├── services/               # API client, WebSocket
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── store/                  # Zustand state stores
│   │   ├── types/                  # TypeScript types
│   │   ├── utils/                  # Utility functions
│   │   ├── styles/                 # CSS/styling
│   │   ├── App.tsx                 # Root component
│   │   └── main.tsx                # Entry point
│   ├── public/                      # Static assets
│   ├── tests/                       # Frontend tests
│   ├── package.json                 # Node.js dependencies
│   ├── .env.example                 # Frontend env configuration
│   ├── tsconfig.json                # TypeScript config
│   ├── vite.config.ts               # Vite build config
│   ├── README.md                    # Frontend documentation
│   ├── Dockerfile                   # Frontend containerization
│   └── .dockerignore                # Docker ignore file
│
├── docs/                            # Shared documentation
│   ├── ARCHITECTURE.md              # System architecture
│   ├── BACKEND_HLD.md               # Backend high-level design
│   ├── API_SPECIFICATION.md         # API endpoints & schemas
│   ├── DEPLOYMENT.md                # Deployment guide
│   └── DEVELOPMENT.md               # Development guide
│
├── docker-compose.yml               # Run both locally
├── README.md                        # Root-level documentation
├── .gitignore                       # Git ignore rules
└── PROJECT_STRUCTURE.md             # This file
```

## Building & Deploying Independently

### Backend (Python/FastAPI)

**Install & Run**:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs on: `http://localhost:8000`

**Build Docker Image**:
```bash
cd backend
docker build -t ai-finance-backend .
docker run -p 8000:8000 ai-finance-backend
```

### Frontend (React/TypeScript)

**Install & Run**:
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

**Build Docker Image**:
```bash
cd frontend
docker build -t ai-finance-frontend .
docker run -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8000 \
  ai-finance-frontend
```

## Running Both Together

**Using Docker Compose**:
```bash
# From root directory
docker-compose up
```

Both services will start:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Environment Configuration

### Backend Configuration
File: `backend/.env.example`
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
DATABASE_URL=...
```

### Frontend Configuration
File: `frontend/.env.example`
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Development Workflow

### Changing Backend
1. Modify files in `backend/src/`
2. Tests: `cd backend && python -m pytest`
3. Restart: `python main.py`

### Changing Frontend
1. Modify files in `frontend/src/`
2. Hot reload automatically (Vite dev server)
3. Tests: `cd frontend && npm test`

### Deploying Backend Only
```bash
cd backend
# Deploy to production server
docker build -t myregistry/backend:latest .
docker push myregistry/backend:latest
```

### Deploying Frontend Only
```bash
cd frontend
# Deploy to Vercel, Netlify, or similar
npm run build
# Upload dist/ folder to hosting
```

## Package Managers

| Package Type | Tool | File |
|--------------|------|------|
| Backend (Python) | pip | `backend/requirements.txt` |
| Frontend (Node.js) | npm | `frontend/package.json` |

## CI/CD

Each package can have its own CI/CD pipeline:

- **Backend CI**: Test Python code, type checking, linting
- **Frontend CI**: Test React components, TypeScript checking, bundle analysis

Example GitHub Actions workflows in `.github/workflows/`:
- `backend-tests.yml` - Backend testing
- `frontend-tests.yml` - Frontend testing
- `deploy-backend.yml` - Backend deployment
- `deploy-frontend.yml` - Frontend deployment

## Deployment Architectures

### Monolith Deployment (same server)
```
Server (VPS/EC2):
  ├── Backend (FastAPI, port 8000)
  └── Frontend (Nginx, port 3000)
```

### Microservices Deployment (separate servers)
```
Backend Server:
  └── Backend (FastAPI, port 8000)

Frontend Server:
  └── Frontend (Nginx, port 3000)
```

### Serverless Deployment
```
Backend: AWS Lambda + API Gateway
Frontend: CloudFront + S3
```

## Summary

✅ Backend and Frontend are **completely independent**
✅ Each has its own dependencies (requirements.txt vs package.json)
✅ Each can be built, tested, and deployed separately
✅ Can run together with docker-compose or separately
✅ Clear configuration for different environments

Start developing either package without touching the other!
