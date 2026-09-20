import path from "node:path";
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, "");
  // Where the FastAPI server lives during local development.
  const backendUrl = env.VITE_DEV_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { "@": path.resolve(rootDir, "src") },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.ts"],
      css: false,
    },
    server: {
      port: 5173,
      host: true,
      // The browser calls a same-origin "/api/...", Vite forwards it to FastAPI.
      // This mirrors production, where nginx does the same thing (no CORS needed).
      proxy: {
        "/api": { target: backendUrl, changeOrigin: true },
      },
    },
  };
});
