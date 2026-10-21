import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Send /api calls to the FastAPI backend so the browser sees one address.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
