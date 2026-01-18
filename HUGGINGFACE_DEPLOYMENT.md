# Deploy AI Finance Assistant to HuggingFace Spaces

## Overview

You'll deploy **2 separate Spaces** on HuggingFace:
1. **Backend** (FastAPI on port 8000)
2. **Frontend** (React on port 5173)

---

## Prerequisites

1. HuggingFace account (https://huggingface.co)
2. Your code on GitHub (✅ Already done!)
3. API keys:
   - OPENAI_API_KEY
   - PINECONE_API_KEY
   - PINECONE_INDEX_NAME

---

## PART 1: Deploy Backend to HuggingFace Spaces

### Step 1: Create Backend Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in:
   - **Space name:** `AIFinanceAssistant-Backend`
   - **License:** Open Licence (or your choice)
   - **Space SDK:** Docker
   - **Space hardware:** CPU (or GPU if budget allows)
4. Click "Create Space"

### Step 2: Add Dockerfile for Backend

In the new space, create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY .env .env

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "src.web_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 3: Add Files to Backend Space

Upload these files to the backend space:
- `requirements.txt`
- `src/` (entire folder)
- `.env.example` (rename to `.env` and fill in your keys)

### Step 4: Set Environment Variables

In the space settings:
1. Go to **Settings** → **Variables and secrets**
2. Add:
   - `OPENAI_API_KEY`: Your OpenAI key
   - `PINECONE_API_KEY`: Your Pinecone key
   - `PINECONE_INDEX_NAME`: Your index name

Backend will be available at:
```
https://your-username-aifinanceassistant-backend.hf.space
```

---

## PART 2: Deploy Frontend to HuggingFace Spaces

### Step 1: Create Frontend Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in:
   - **Space name:** `AIFinanceAssistant-Frontend`
   - **License:** Open Licence
   - **Space SDK:** Docker
   - **Space hardware:** CPU
4. Click "Create Space"

### Step 2: Add Dockerfile for Frontend

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/*.html ./
COPY frontend/*.ts ./
COPY frontend/*.js ./
COPY frontend/tsconfig.json ./
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./

# Build the app
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Step 3: Add nginx.conf for Frontend

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass https://your-username-aifinanceassistant-backend.hf.space/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 4: Update Frontend API Configuration

In `frontend/src/config/index.ts`, update:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-username-aifinanceassistant-backend.hf.space';

export { API_BASE_URL };
```

### Step 5: Upload Frontend Files

Upload to frontend space:
- `frontend/` (entire folder)
- `Dockerfile`
- `nginx.conf`

Frontend will be available at:
```
https://your-username-aifinanceassistant-frontend.hf.space
```

---

## ALTERNATIVE: Deploy Both in One Docker Space

If you prefer to run both services in a single Docker container:

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
    networks:
      - app-network

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

But **separate spaces is recommended** for easier management.

---

## Step-by-Step Deployment Summary

### For Backend Space:

```bash
# 1. Create space on HuggingFace (Docker SDK)
# 2. Upload files:
#    - Dockerfile
#    - requirements.txt
#    - src/ folder
#    - .env file (with your API keys)
# 3. Set environment variables in space settings
# 4. Space will build and run automatically
```

### For Frontend Space:

```bash
# 1. Create space on HuggingFace (Docker SDK)
# 2. Upload files:
#    - Dockerfile
#    - nginx.conf
#    - frontend/ folder
# 3. Update API URL in frontend config
# 4. Space will build and run automatically
```

---

## Verify Deployment

After spaces are built:

1. **Backend Health Check:**
   ```bash
   curl https://your-username-aifinanceassistant-backend.hf.space/health
   # Should return: {"status": "ok", "version": "0.1.0"}
   ```

2. **Frontend:**
   ```
   https://your-username-aifinanceassistant-frontend.hf.space
   # Should load the dashboard
   ```

3. **Test Chat:**
   - Go to frontend
   - Send a message in chat
   - Should get response from backend

---

## Troubleshooting

### Backend not responding:
1. Check space logs (Space Settings → Logs)
2. Verify API keys are set in environment variables
3. Check Pinecone connection

### Frontend can't connect to backend:
1. Check nginx.conf proxy_pass URL
2. Verify backend space URL is correct
3. Check CORS is enabled in FastAPI

### Build fails:
1. Check logs in HuggingFace space
2. Verify all files are uploaded
3. Check Python/Node versions match local

---

## Environment Variables Needed

**Backend (.env file):**
```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=ai-finance-knowledge-base
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend (.env):**
```
REACT_APP_API_URL=https://your-username-aifinanceassistant-backend.hf.space
```

---

## Cost Considerations

HuggingFace Spaces:
- **Free tier:** Limited resources (CPU only, 2GB RAM)
- **Paid tier:** Better performance (~$7.50/month per space)

For this project, free tier might be slow. Consider upgrading to paid for better experience.

---

## Quick Reference URLs

After deployment:
- **Frontend:** `https://your-username-aifinanceassistant-frontend.hf.space`
- **Backend:** `https://your-username-aifinanceassistant-backend.hf.space`
- **Backend Health:** `https://your-username-aifinanceassistant-backend.hf.space/health`

---

## Summary

1. ✅ Create 2 spaces (Backend + Frontend)
2. ✅ Add Dockerfiles
3. ✅ Upload code from GitHub
4. ✅ Set environment variables
5. ✅ HuggingFace builds automatically
6. ✅ Access via provided URLs

**Both services will be live!** 🚀
