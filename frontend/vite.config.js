import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // dev proxy → FastAPI, so the frontend calls same-origin paths
      "/report": "http://127.0.0.1:8000",
      "/feed": "http://127.0.0.1:8000",
      "/families": "http://127.0.0.1:8000",
      "/graph": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
