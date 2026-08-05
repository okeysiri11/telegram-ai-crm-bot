/**
 * Vite middleware — Sprint 29.2 Life Engine REST.
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

export function lifeApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-life",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-life/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.2",
            service: "enterprise-life",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.2",
            endpoints: ["GET /health", "GET /city", "GET /occupancy", "GET /timeline", "GET /events"],
          });
        }

        if (path.endsWith("/city") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.2",
            citizens: [],
            occupancy: [],
            meetings: [],
            vehicles: [],
            activities: [],
            ai: [],
            projects: [],
            movements: [],
            stats: { events: 0, online: 0, activeMeetings: 0, inTransit: 0 },
            note: "Use lifeEngine.cityRuntime() in-process for live data",
          });
        }

        if (path.endsWith("/occupancy") && method === "GET") {
          return sendJson(res, 200, { occupancy: [] });
        }

        if (path.endsWith("/timeline") && method === "GET") {
          return sendJson(res, 200, { timeline: [] });
        }

        if (path.endsWith("/events") && method === "GET") {
          return sendJson(res, 200, { events: [] });
        }

        return sendJson(res, 404, { error: "life_route_not_found", path });
      });
    },
  };
}
