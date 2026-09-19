import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The API is proxied so the app and API share one origin: the HttpOnly session
// cookie then works without any CORS or credentials configuration.
// 127.0.0.1, not localhost: Node resolves localhost to IPv6 first, uvicorn listens on IPv4.
const API = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/auth": API,
      "/workspace": API,
    },
  },
});
