/**
 * Vite middleware — Sprint 29.9 Kernel REST.
 */

import type { Plugin } from "vite";
import type { ServerResponse } from "node:http";

function sendJson(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function pathOnly(url: string) {
  return url.split("?")[0] || url;
}

export function kernelApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-kernel",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-kernel/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.9",
            service: "enterprise-kernel",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.9",
            endpoints: [
              "GET /health",
              "GET /status",
              "GET /diagnostics",
              "GET /boot-sequence",
              "GET /modules",
              "GET /recovery",
              "GET /config",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/status") && method === "GET") {
          return sendJson(res, 200, { phase: "ready", ready: true, note: "in-process" });
        }
        if (path.endsWith("/diagnostics") && method === "GET") {
          return sendJson(res, 200, { id: null, note: "in-process" });
        }
        if (path.endsWith("/boot-sequence") && method === "GET") {
          return sendJson(res, 200, { steps: [] });
        }
        if (path.endsWith("/modules") && method === "GET") {
          return sendJson(res, 200, { modules: [] });
        }
        if (path.endsWith("/recovery") && method === "GET") {
          return sendJson(res, 200, { history: [] });
        }
        if (path.endsWith("/config") && method === "GET") {
          return sendJson(res, 200, { version: "29.9" });
        }

        return sendJson(res, 404, { error: "kernel_route_not_found", path });
      });
    },
  };
}
