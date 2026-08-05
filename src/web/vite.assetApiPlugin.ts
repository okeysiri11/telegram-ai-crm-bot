/**
 * Vite middleware — Sprint 29.3 Asset Runtime REST.
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

export function assetApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-assets",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-assets/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.3",
            service: "enterprise-assets",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.3",
            endpoints: [
              "GET /health",
              "GET /assets",
              "GET /city",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/assets") && method === "GET") {
          return sendJson(res, 200, { assets: [] });
        }

        if (path.endsWith("/city") && method === "GET") {
          return sendJson(res, 200, {
            byBuilding: {},
            byCompany: {},
            byCitizen: {},
            byDistrict: {},
            totals: { assets: 0, available: 0, inUse: 0, maintenance: 0 },
            note: "Use assetRuntime.cityQuery() in-process for live data",
          });
        }

        return sendJson(res, 404, { error: "asset_route_not_found", path });
      });
    },
  };
}
