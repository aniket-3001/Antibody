import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // dev proxy → FastAPI, so the frontend calls same-origin paths
      "/report": "http://127.0.0.1:8000",
      "/feed": "http://127.0.0.1:8000",
      "/families": "http://127.0.0.1:8000",
      "/graph": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/leaderboard": "http://127.0.0.1:8000",
      "/scan": "http://127.0.0.1:8000",
      "/reporter": "http://127.0.0.1:8000",
      // Help chatbot — separate process/port (help_api/), separate Cognee
      // memory base from the scam graph above.
      "/help": "http://127.0.0.1:8010",
    },
  },
});
