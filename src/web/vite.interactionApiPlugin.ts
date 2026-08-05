/**
 * Vite middleware — Sprint 29.6 Interaction Runtime REST.
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

export function interactionApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-interaction",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-interaction/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.6",
            service: "enterprise-interaction",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.6",
            endpoints: [
              "GET /health",
              "GET /sessions",
              "GET /selection",
              "GET /search",
              "GET /navigation",
              "GET /actions",
              "GET /history",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/sessions") && method === "GET") {
          return sendJson(res, 200, { sessions: [], note: "in-process engine" });
        }
        if (path.endsWith("/selection") && method === "GET") {
          return sendJson(res, 200, { mode: "single", targets: [], revision: 0 });
        }
        if (path.endsWith("/search") && method === "GET") {
          return sendJson(res, 200, { hits: [] });
        }
        if (path.endsWith("/navigation") && method === "GET") {
          return sendJson(res, 200, { history: [] });
        }
        if (path.endsWith("/actions") && method === "GET") {
          return sendJson(res, 200, { actions: [] });
        }
        if (path.endsWith("/history") && method === "GET") {
          return sendJson(res, 200, { history: [] });
        }

        return sendJson(res, 404, { error: "interaction_route_not_found", path });
      });
    },
  };
}
