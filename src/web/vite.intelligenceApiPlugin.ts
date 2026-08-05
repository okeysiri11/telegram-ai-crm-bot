/**
 * Vite middleware — Sprint 29.7 Intelligence Runtime REST.
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

export function intelligenceApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-intelligence",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-intelligence/v1")) return next();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.7",
            service: "enterprise-intelligence",
            mode: "local_vite",
            advisoryOnly: true,
            autonomousExecution: false,
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.7",
            policy: { autonomousExecution: false, recommendationsRequireApproval: true },
            endpoints: [
              "GET /health",
              "GET /insights",
              "GET /recommendations",
              "GET /trends",
              "GET /risks",
              "GET /analytics",
              "GET /inventory",
            ],
          });
        }

        for (const key of ["insights", "recommendations", "trends", "risks"]) {
          if (path.endsWith(`/${key}`) && method === "GET") {
            return sendJson(res, 200, { [key]: [], note: "in-process engine" });
          }
        }

        if (path.endsWith("/analytics") && method === "GET") {
          return sendJson(res, 200, {
            businessActivity: 0,
            workflowBottlenecks: 0,
            citizenOnline: 0,
            assetUtilizationPct: 0,
            partnerRelations: 0,
            projectHealth: 0,
            districtActivityAvg: 0,
            openRisks: 0,
            insightCount: 0,
            recommendationCount: 0,
          });
        }

        return sendJson(res, 404, { error: "intelligence_route_not_found", path });
      });
    },
  };
}
