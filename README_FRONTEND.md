# AI Finance Assistant - Frontend

React/TypeScript web interface for the AI Finance Assistant backend.

## Quick Start

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0

### Installation

1. **Clone/Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure Backend Server**:
   
   Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local` and update the backend URLs:
   ```env
   # Development (local backend)
   VITE_API_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000

   # Production (remote backend)
   # VITE_API_URL=https://api.example.com
   # VITE_WS_URL=wss://api.example.com
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Configuration

### Environment Variables

All configuration is done through environment variables defined in `.env.local`.

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend REST API base URL | `http://localhost:8000` |
| `VITE_WS_URL` | Backend WebSocket URL | `ws://localhost:8000` |
| `VITE_ENV` | Environment type | `development` |
| `VITE_LOG_LEVEL` | Logging level | `info` |
| `VITE_ENABLE_DEBUG` | Enable debug mode | `false` |
| `VITE_ENABLE_DARK_MODE` | Enable dark mode | `true` |
| `VITE_ENABLE_WEBSOCKET_STREAMING` | Enable WebSocket streaming | `true` |
| `VITE_ENABLE_PORTFOLIO_ANALYSIS` | Enable portfolio analysis | `true` |

### Backend Configuration Examples

**Local Development**:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Staging**:
```env
VITE_API_URL=https://staging-api.example.com
VITE_WS_URL=wss://staging-api.example.com
```

**Production**:
```env
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
```

## Development

### Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm run test` | Run tests with Vitest |
| `npm run test:ui` | Run tests with UI |
| `npm run test:coverage` | Generate coverage report |

### Project Structure

```
src/
├── config/          # Configuration management
├── services/        # API and utility services
├── hooks/           # Custom React hooks
├── store/           # Zustand state stores
├── types/           # TypeScript type definitions
├── components/      # React components
├── pages/           # Page components
├── styles/          # CSS and styling
└── utils/           # Utility functions
```

## API Integration

The frontend communicates with the backend via:

1. **REST API** - Synchronous requests
   - Query endpoint: `POST /api/chat/finance-qa`
   - History endpoint: `GET /api/chat/history/:sessionId`

2. **WebSocket** - Streaming responses
   - Connection: `WS /ws/chat`
   - Real-time message streaming

See [FRONTEND_DEV_LOG.md](./FRONTEND_DEV_LOG.md) for detailed API specifications.

## Building & Deployment

### Build for Production

```bash
npm run build
```

Creates optimized production build in `dist/` folder.

### Deploy to Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Deploy with Docker

```bash
docker build -t ai-finance-frontend .
docker run -p 3000:3000 \
  -e VITE_API_URL=https://api.example.com \
  -e VITE_WS_URL=wss://api.example.com \
  ai-finance-frontend
```

## Testing

Run all tests:
```bash
npm run test
```

Run with UI:
```bash
npm run test:ui
```

Generate coverage:
```bash
npm run test:coverage
```

## Performance

Current performance targets:
- Lighthouse score: > 90
- First Contentful Paint: < 1.5s
- Bundle size: < 250KB (gzipped)
- API latency: < 500ms (backend dependent)

Check performance:
```bash
npm run build
npm run preview
# Then run Lighthouse audit in Chrome DevTools
```

## Troubleshooting

### Cannot connect to backend

1. Verify backend is running on the configured URL
2. Check `VITE_API_URL` and `VITE_WS_URL` in `.env.local`
3. Ensure CORS is enabled on backend
4. Check browser console for detailed error messages

### Build errors

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules
   npm install
   ```

2. Clear Vite cache:
   ```bash
   rm -rf dist
   npm run build
   ```

### Port 5173 already in use

Change the port:
```bash
npm run dev -- --port 3000
```

## Dependencies

See [package.json](./package.json) for the complete list of dependencies.

Key packages:
- **React 18.x** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React Router** - Navigation
- **Vitest** - Testing framework

## Contributing

1. Follow the code style (ESLint, Prettier)
2. Write tests for new features
3. Update documentation
4. Create a pull request

## License

MIT

## Support

For issues or questions:
1. Check [FRONTEND_DEV_LOG.md](./FRONTEND_DEV_LOG.md) for detailed documentation
2. Check backend logs for API errors
3. Enable debug mode: `VITE_ENABLE_DEBUG=true`
