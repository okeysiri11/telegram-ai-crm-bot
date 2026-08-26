/// <reference types="vitest/config" />
import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import type { ProxyOptions } from "vite";
import type { ServerResponse } from "node:http";
import { Socket } from "node:net";
import { demoAuthPlugin } from "./vite.demoAuthPlugin";
import { ebnApiPlugin } from "./vite.ebnApiPlugin";
import { edcApiPlugin } from "./vite.edcApiPlugin";
import { lifeApiPlugin } from "./vite.lifeApiPlugin";
import { assetApiPlugin } from "./vite.assetApiPlugin";
import { spatialApiPlugin } from "./vite.spatialApiPlugin";
import { cityVizApiPlugin } from "./vite.cityVizApiPlugin";
import { interactionApiPlugin } from "./vite.interactionApiPlugin";
import { intelligenceApiPlugin } from "./vite.intelligenceApiPlugin";
import { orchestratorApiPlugin } from "./vite.orchestratorApiPlugin";
import { kernelApiPlugin } from "./vite.kernelApiPlugin";

/** Fail-safe: never treat VITE_DEMO_AUTH as a production bypass. */
function demoAuthProductionGuard(): Plugin {
  return {
    name: "ados-demo-auth-prod-guard",
    config(_cfg, { command, mode }) {
      if (command !== "build" || mode !== "production") return;
      delete process.env.VITE_DEMO_AUTH;
      const env = loadEnv(mode, path.resolve(__dirname), "VITE_");
      if (env.VITE_DEMO_AUTH === "true" || process.env.VITE_DEMO_AUTH === "true") {
        console.error(
          "[ADOS] VITE_DEMO_AUTH=true is ignored in production builds. Demo auth bypass is disabled.",
        );
        delete process.env.VITE_DEMO_AUTH;
      }
      return {
        define: {
          "import.meta.env.VITE_DEMO_AUTH": JSON.stringify(""),
        },
      };
    },
  };
}

function writeProxyUnavailable(
  res: ServerResponse | Socket,
  detail: string,
  cause: string,
) {
  if (!(res instanceof Socket) && !res.headersSent) {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        ok: false,
        error: "api_unavailable",
        detail,
        cause,
      }),
    );
  }
}

function apiProxyConfig(): Record<string, ProxyOptions> {
  const target = process.env.VITE_API_PROXY || "http://127.0.0.1:8080";
  return {
    "/api": {
      target,
      changeOrigin: true,
      configure(proxy) {
        proxy.on("error", (err: Error, _req: unknown, res: ServerResponse | Socket) => {
          writeProxyUnavailable(
            res,
            "Backend on :8080 is not reachable. Run: npm run dev:all (or scripts/run_api_local.py).",
            err?.message || String(err),
          );
        });
      },
      bypass(req: { url?: string }) {
        if (req.url?.startsWith("/api/enterprise-demo-auth/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-ebn/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-edc/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-life/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-assets/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-spatial/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-city-viz/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-interaction/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-intelligence/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-orchestrator/v1")) return req.url;
        if (req.url?.startsWith("/api/enterprise-kernel/v1")) return req.url;
        return undefined;
      },
    },
    "/management": {
      target,
      changeOrigin: true,
      configure(proxy) {
        proxy.on("error", (err: Error, _req: unknown, res: ServerResponse | Socket) => {
          writeProxyUnavailable(
            res,
            "Backend on :8080 is not reachable. Run: npm run dev:all.",
            err?.message || String(err),
          );
        });
      },
    },
  };
}

export default defineConfig(({ command }) => {
  const localEnv =
    command === "serve" ? loadEnv("development", path.resolve(__dirname), "") : {};
  return {
  define: {
    "import.meta.env.VITE_API_PROXY": JSON.stringify(""),
  },
  plugins: [
    react(),
    tailwindcss(),
    demoAuthProductionGuard(),
    demoAuthPlugin(),
    ebnApiPlugin(),
    edcApiPlugin(),
    lifeApiPlugin(),
    assetApiPlugin(),
    spatialApiPlugin(),
    cityVizApiPlugin(),
    interactionApiPlugin(),
    intelligenceApiPlugin(),
    orchestratorApiPlugin(),
    kernelApiPlugin(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: process.env.VITE_DEV_HOST || localEnv.VITE_DEV_HOST || "127.0.0.1",
    port: Number(process.env.PORT || process.env.VITE_PORT || localEnv.PORT || 5180),
    strictPort: Boolean(process.env.VITE_STRICT_PORT === "1"),
    headers: {
      "Cache-Control": "no-store",
    },
    allowedHosts: [
      ".trycloudflare.com",
      ".cfargotunnel.com",
      "localhost",
      "127.0.0.1",
    ],
    proxy: apiProxyConfig(),
  },
  preview: {
    host: process.env.VITE_DEV_HOST || "0.0.0.0",
    port: Number(process.env.VITE_PREVIEW_PORT || 4173),
    strictPort: Boolean(process.env.VITE_STRICT_PORT === "1"),
    allowedHosts: [
      ".trycloudflare.com",
      ".cfargotunnel.com",
      "localhost",
      "127.0.0.1",
    ],
    proxy: apiProxyConfig(),
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
};
});
