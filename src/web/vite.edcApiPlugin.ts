/**
 * Vite middleware — Sprint 29.1 Digital Citizen REST API.
 * Serves /api/enterprise-edc/v1 when Hub backend is absent.
 */

import type { Plugin } from "vite";
import type { IncomingMessage, ServerResponse } from "node:http";
import { Buffer } from "node:buffer";

type Citizen = {
  id: string;
  displayName: string;
  presence: { status: string; cityBuildingId?: string; officeId?: string };
  role?: string;
};

const citizens = new Map<string, Citizen>();

function seed() {
  if (citizens.size) return;
  citizens.set("cit_owner_demo", {
    id: "cit_owner_demo",
    displayName: "Owner Demo",
    presence: { status: "online", cityBuildingId: "hub", officeId: "hq_floor_1" },
    role: "owner",
  });
  citizens.set("cit_dev_alex", {
    id: "cit_dev_alex",
    displayName: "Alex Developer",
    presence: { status: "busy", cityBuildingId: "ai_studio" },
    role: "member",
  });
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (c) => chunks.push(Buffer.from(c)));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function sendJson(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function pathOnly(url: string) {
  return url.split("?")[0] || url;
}

export function edcApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-edc",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-edc/v1")) return next();
        seed();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.1",
            service: "enterprise-edc",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.1",
            citizens: citizens.size,
            endpoints: [
              "GET /health",
              "GET /citizens",
              "GET /presence",
              "POST /presence",
              "GET /city/:id",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/citizens") && method === "GET") {
          return sendJson(res, 200, { citizens: [...citizens.values()] });
        }

        const citizenMatch = path.match(/\/citizens\/([^/]+)$/);
        if (citizenMatch && method === "GET") {
          const c = citizens.get(decodeURIComponent(citizenMatch[1]!));
          if (!c) return sendJson(res, 404, { error: "not_found" });
          return sendJson(res, 200, { citizen: c });
        }

        if (path.endsWith("/presence") && method === "GET") {
          return sendJson(res, 200, {
            presence: [...citizens.values()].map((c) => ({
              citizenId: c.id,
              displayName: c.displayName,
              status: c.presence.status,
              cityBuildingId: c.presence.cityBuildingId,
              officeId: c.presence.officeId,
            })),
          });
        }

        if (path.endsWith("/presence") && method === "POST") {
          try {
            const body = JSON.parse((await readBody(req)) || "{}") as {
              citizenId?: string;
              status?: string;
            };
            const c = body.citizenId ? citizens.get(body.citizenId) : undefined;
            if (!c || !body.status) return sendJson(res, 400, { error: "invalid" });
            c.presence = { ...c.presence, status: body.status };
            return sendJson(res, 200, { ok: true });
          } catch {
            return sendJson(res, 400, { error: "invalid_json" });
          }
        }

        const cityMatch = path.match(/\/city\/([^/]+)$/);
        if (cityMatch && method === "GET") {
          const id = decodeURIComponent(cityMatch[1]!);
          const c = citizens.get(id);
          if (!c) return sendJson(res, 404, { error: "not_found" });
          return sendJson(res, 200, {
            facade: {
              citizenId: c.id,
              displayName: c.displayName,
              presence: c.presence.status,
              role: c.role,
              officeId: c.presence.officeId,
              cityBuildingId: c.presence.cityBuildingId,
              aiAssignmentIds: [],
            },
          });
        }

        return sendJson(res, 404, { error: "edc_route_not_found", path });
      });
    },
  };
}
