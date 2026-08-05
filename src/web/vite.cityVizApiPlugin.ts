/**
 * Vite middleware — Sprint 29.5 City Visualization REST.
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

export function cityVizApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-city-viz",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-city-viz/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.5",
            service: "enterprise-city-viz",
            mode: "local_vite",
            city: "Odessa",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.5",
            endpoints: [
              "GET /health",
              "GET /scene",
              "GET /visible",
              "GET /buildings",
              "GET /citizens",
              "GET /companies",
              "GET /assets",
              "GET /activities",
              "GET /districts",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/scene") && method === "GET") {
          return sendJson(res, 200, {
            scene: null,
            note: "Use cityVisualizationRuntime.scene() in-process for live data",
          });
        }

        if (path.endsWith("/visible") && method === "GET") {
          return sendJson(res, 200, {
            buildings: [],
            citizens: [],
            companies: [],
            assets: [],
            activities: [],
            districts: [],
            revision: 0,
            lod: "near",
            note: "Use cityVisualizationRuntime.visibleQuery() in-process",
          });
        }

        for (const key of ["buildings", "citizens", "companies", "assets", "activities", "districts"]) {
          if (path.endsWith(`/${key}`) && method === "GET") {
            return sendJson(res, 200, { [key]: [], note: "in-process engine" });
          }
        }

        return sendJson(res, 404, { error: "city_viz_route_not_found", path });
      });
    },
  };
}
