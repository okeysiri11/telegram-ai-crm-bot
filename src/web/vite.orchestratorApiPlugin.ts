/**
 * Vite middleware — Sprint 29.8 Orchestrator REST.
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

export function orchestratorApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-orchestrator",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-orchestrator/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.8",
            service: "enterprise-orchestrator",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.8",
            endpoints: [
              "GET /health",
              "GET /runtimes",
              "GET /graph",
              "GET /queue",
              "GET /events",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/runtimes") && method === "GET") {
          return sendJson(res, 200, { runtimes: [], note: "in-process engine" });
        }
        if (path.endsWith("/graph") && method === "GET") {
          return sendJson(res, 200, { order: [], edges: [] });
        }
        if (path.endsWith("/queue") && method === "GET") {
          return sendJson(res, 200, { queue: [] });
        }
        if (path.endsWith("/events") && method === "GET") {
          return sendJson(res, 200, { events: [] });
        }

        return sendJson(res, 404, { error: "orchestrator_route_not_found", path });
      });
    },
  };
}
