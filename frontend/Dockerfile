# Frontend Dockerfile - Multi-stage build for React app
# Stage 1: Build React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
# Set backend API URL during build (can be overridden via ARG)
ARG VITE_API_URL=https://vemannem-aifinanceassistant-backend.hf.space
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy nginx config
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 7860;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/javascript application/json;

    # SPA routing - all requests go to index.html
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy - forward to backend
    location /api {
        proxy_pass https://vemannem-aifinanceassistant-backend.hf.space;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Copy built React app from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:7860/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
