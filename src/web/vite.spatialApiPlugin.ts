/**
 * Vite middleware — Sprint 29.4 Spatial Runtime REST.
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

export function spatialApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-spatial",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-spatial/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.4",
            service: "enterprise-spatial",
            mode: "local_vite",
            city: "Odessa",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.4",
            endpoints: [
              "GET /health",
              "GET /hierarchy",
              "GET /districts",
              "GET /buildings",
              "GET /route",
              "GET /city",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/hierarchy") && method === "GET") {
          return sendJson(res, 200, {
            note: "Use spatialRuntime.hierarchy() in-process for live data",
            city: [{ id: "city_odessa", name: "Odessa" }],
          });
        }

        if (path.endsWith("/districts") && method === "GET") {
          return sendJson(res, 200, { districts: [] });
        }

        if (path.endsWith("/buildings") && method === "GET") {
          return sendJson(res, 200, { buildings: [] });
        }

        if (path.endsWith("/route") && method === "GET") {
          return sendJson(res, 200, {
            route: null,
            note: "Use spatialRuntime.route() in-process for live routing",
          });
        }

        if (path.endsWith("/city") && method === "GET") {
          return sendJson(res, 200, {
            buildingsByDistrict: {},
            companiesByBuilding: {},
            citizensByLocation: {},
            assetsByBuilding: {},
            projectsByArea: {},
            meetingsByOffice: {},
            districts: [],
            stats: { entities: 0, buildings: 0, districts: 0, routesCached: 0, assignments: 0 },
            note: "Use spatialRuntime.cityQuery() in-process for live data",
          });
        }

        return sendJson(res, 404, { error: "spatial_route_not_found", path });
      });
    },
  };
}
