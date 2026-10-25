import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the browser talks to Vite (port 5173).
// Vite forwards /api and /uploads to the FastAPI backend (port 8000), so there are no CORS problems.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/uploads": "http://127.0.0.1:8000",
    },
  },
});
