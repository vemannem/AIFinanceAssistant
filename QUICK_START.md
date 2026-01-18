# Quick Reference - Two Packages Setup

## What You Have Now

✅ **Backend Package** (Python)
- Location: `/backend`
- Dependencies: `requirements.txt`
- Run: `cd backend && python main.py`
- Port: 8000

✅ **Frontend Package** (Node.js)
- Location: `/frontend`
- Dependencies: `package.json`
- Run: `cd frontend && npm install && npm run dev`
- Port: 5173

✅ **Docker Compose**
- Run both together: `docker-compose up`
- Requires `.env` file in root with API keys

## Installation

```bash
# Backend (Python)
cd backend
pip install -r requirements.txt
python main.py

# Frontend (Node.js) - in another terminal
cd frontend
npm install
npm run dev
```

## Configuration

### Frontend Backend URL

Edit `frontend/.env.local`:
```env
# Local backend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Remote backend
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
```

### Backend API Keys

Create `backend/.env`:
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=gcp-starter
```

## Files Created

### Frontend Setup Files
1. `package.json` - npm dependencies list
2. `.env.example` - backend URL template
3. `.env.local` - local configuration
4. `src/config/index.ts` - ConfigManager
5. `src/services/api.ts` - API client
6. `README_FRONTEND.md` - setup guide

### Documentation Files
1. `README.md` - root documentation
2. `PROJECT_STRUCTURE.md` - detailed layout
3. `TWO_PACKAGE_GUIDE.md` - architecture guide
4. `SETUP_SUMMARY.md` - setup summary
5. `docker-compose.yml` - Docker Compose config

## Deploy Independently

### Deploy Backend Only
```bash
cd backend
docker build -t backend:latest .
docker run -p 8000:8000 backend:latest
```

### Deploy Frontend Only
```bash
cd frontend
npm run build
# Upload dist/ folder to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Your own server
```

## Features

✅ Completely independent packages
✅ Different dependency managers (pip vs npm)
✅ Separate configuration files
✅ Deploy to different servers
✅ Scale independently
✅ Different tech stacks

## Next: Continue Week 1 Development

→ [FRONTEND_DEV_LOG.md](FRONTEND_DEV_LOG.md) - Week 1 plan
→ [README_FRONTEND.md](README_FRONTEND.md) - Frontend setup
