# Two-Package Architecture Guide

## Overview

The AI Finance Assistant is organized as **two completely independent packages**:

| Package | Type | Location | Manager | Entry Point |
|---------|------|----------|---------|-------------|
| **Backend** | FastAPI (Python) | `/backend` | pip | `python main.py` |
| **Frontend** | React (TypeScript) | `/frontend` | npm | `npm run dev` |

Each package has its own:
- Dependency file (requirements.txt vs package.json)
- Configuration (.env file)
- Tests (pytest vs Jest/Vitest)
- Docker container
- Deployment process

## Quick Commands

### Backend Only

```bash
# Install
cd backend
pip install -r requirements.txt

# Run
python main.py

# Test
pytest tests/ -v

# Build Docker
docker build -t backend:latest .
```

### Frontend Only

```bash
# Install
cd frontend
npm install

# Run
npm run dev

# Test
npm test

# Build Docker
docker build -t frontend:latest .
```

### Both Together

```bash
# Using Docker Compose (requires .env file)
docker-compose up

# Manual (2 terminals)
# Terminal 1:
cd backend && python main.py

# Terminal 2:
cd frontend && npm run dev
```

## Environment Variables

### Backend (.env file in root or `/backend`)
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=gcp-starter
DATABASE_URL=postgresql://...
```

### Frontend (.env.local file in `/frontend`)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_LOG_LEVEL=debug
```

## Deployment Scenarios

### Scenario 1: Develop Backend Only (Frontend as client)
```bash
cd backend
pip install -r requirements.txt
python main.py

# Frontend can be built separately or run from another machine
# pointing to backend URL
```

### Scenario 2: Develop Frontend Only (Backend already running)
```bash
# Backend runs on production or another server
cd frontend
npm install
# Update .env.local with backend URL
npm run dev
```

### Scenario 3: Deploy Backend to Production
```bash
cd backend
docker build -t myregistry/backend:v1.0.0 .
docker push myregistry/backend:v1.0.0
# Deploy to AWS ECS, Google Cloud Run, Kubernetes, etc.
```

### Scenario 4: Deploy Frontend to Production
```bash
cd frontend
npm run build
# Upload dist/ folder to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - GitHub Pages
# - Your own server (nginx)
```

### Scenario 5: Deploy Both Together
```bash
docker-compose build
docker-compose push
# Deploy stack to Docker Swarm, Kubernetes, etc.
```

## Key Differences

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Package Manager**: pip
- **Dependencies**: requirements.txt
- **Entry Point**: python main.py
- **Port**: 8000 (REST API)
- **Type Safety**: Type hints

### Frontend
- **Language**: TypeScript
- **Framework**: React 18
- **Package Manager**: npm
- **Dependencies**: package.json
- **Entry Point**: npm run dev
- **Port**: 5173 (dev) or 3000 (prod)
- **Type Safety**: TypeScript + strict mode

## File Structure

```
AIFinanceAssistent/
├── backend/                     ← Complete Python project
│   ├── src/
│   ├── tests/
│   ├── requirements.txt         ← Backend dependencies
│   ├── main.py
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                    ← Complete React project
│   ├── src/
│   ├── tests/
│   ├── package.json             ← Frontend dependencies
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── README.md
│
├── docs/                        ← Shared documentation
├── docker-compose.yml           ← Run both together
├── README.md                    ← Root documentation
└── PROJECT_STRUCTURE.md         ← Detailed structure
```

## Testing Independently

### Backend Tests
```bash
cd backend
pytest tests/ -v                 # All tests
pytest tests/test_api.py -v     # Specific test file
pytest --cov=src tests/          # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test                         # All tests
npm test -- ChatInterface        # Specific component
npm run test:coverage            # With coverage
```

## Building Docker Images Separately

### Build Backend Only
```bash
docker build -t ai-finance-backend:latest ./backend
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e PINECONE_API_KEY=... \
  ai-finance-backend:latest
```

### Build Frontend Only
```bash
docker build -t ai-finance-frontend:latest ./frontend
docker run -p 3000:3000 \
  -e VITE_API_URL=https://api.example.com \
  -e VITE_WS_URL=wss://api.example.com \
  ai-finance-frontend:latest
```

## CI/CD Pipeline

Each package can have independent pipelines:

### Backend CI (GitHub Actions)
```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest tests/
```

### Frontend CI (GitHub Actions)
```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd frontend && npm install
      - run: cd frontend && npm test
```

## Production Deployment

### Option 1: Separate Servers
```
Server A (Backend):
  - Backend on port 8000
  - Database connection

Server B (Frontend):
  - Frontend served by Nginx
  - Points to Server A for API
```

### Option 2: Same Server (Monolith)
```
Single Server:
  - Backend on port 8000
  - Frontend (Nginx) on port 3000
  - Both in Docker containers
  - docker-compose for orchestration
```

### Option 3: Managed Services
```
Frontend: Vercel or Netlify
Backend: AWS Lambda, Google Cloud Run, or Heroku
Database: AWS RDS or Cloud SQL
```

## Summary

✅ **Complete Independence**: Backend and frontend can be developed, tested, and deployed separately  
✅ **Flexible Deployment**: Deploy one, both, or in different environments  
✅ **Clear Separation**: Each package has its own dependencies and configuration  
✅ **Easy Scaling**: Scale backend and frontend independently based on load  
✅ **Multiple Options**: Monolith, microservices, serverless - your choice  

**Next Steps**:
1. [Backend Development](backend/README.md)
2. [Frontend Development](frontend/README.md)
3. [Deployment Guide](docs/DEPLOYMENT.md)
