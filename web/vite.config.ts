import path from "node:path";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const devApiTarget =
    (env.VITE_HARNEX_API_URL && env.VITE_HARNEX_API_URL.replace(/\/$/, "")) ||
    "http://127.0.0.1:8000";
  return {
    plugins: [
      TanStackRouterVite({
        routesDirectory: "src/routes",
        generatedRouteTree: "src/routeTree.gen.ts",
      }),
      react(),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/v1": {
          target: devApiTarget,
          changeOrigin: true,
        },
        "/mcp": {
          target: devApiTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
