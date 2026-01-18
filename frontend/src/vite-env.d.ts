/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_ENV: string;
  readonly VITE_LOG_LEVEL: string;
  readonly VITE_ENABLE_DEBUG: string;
  readonly VITE_ENABLE_DARK_MODE: string;
  readonly VITE_ENABLE_WEBSOCKET_STREAMING: string;
  readonly VITE_ENABLE_PORTFOLIO_ANALYSIS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
