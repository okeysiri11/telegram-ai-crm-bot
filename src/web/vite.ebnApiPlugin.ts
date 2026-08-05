/**
 * Vite middleware — Sprint 29.0 Enterprise Business Network REST API.
 * Serves /api/enterprise-ebn/v1 when Enterprise Hub backend is absent.
 * Mirrors production contract; in-process store for local foundation.
 */

import type { Plugin } from "vite";
import type { IncomingMessage, ServerResponse } from "node:http";
import { Buffer } from "node:buffer";

type Profile = {
  id: string;
  companyName: string;
  category: string;
  status: string;
  verificationStatus: string;
  trustLevel: number;
  headquarters?: string;
  visibility: string;
  ownerOrgId: string;
};

type Relationship = {
  id: string;
  fromProfileId: string;
  toProfileId: string;
  type: string;
  state: string;
};

const profiles = new Map<string, Profile>();
const relationships = new Map<string, Relationship>();

function seed() {
  if (profiles.size) return;
  profiles.set("biz_demo_corp", {
    id: "biz_demo_corp",
    companyName: "Demo Corp",
    category: "technology",
    status: "active",
    verificationStatus: "verified",
    trustLevel: 82,
    headquarters: "Enterprise City · Hub Plaza",
    visibility: "partners",
    ownerOrgId: "org_demo_corp",
  });
  profiles.set("biz_northwind", {
    id: "biz_northwind",
    companyName: "Northwind Partners",
    category: "services",
    status: "active",
    verificationStatus: "verified",
    trustLevel: 74,
    visibility: "partners",
    ownerOrgId: "org_northwind",
  });
  relationships.set("rel_seed_1", {
    id: "rel_seed_1",
    fromProfileId: "biz_demo_corp",
    toProfileId: "biz_northwind",
    type: "strategic_partner",
    state: "approved",
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
  const raw = JSON.stringify(body);
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(raw);
}

function pathOnly(url: string) {
  return url.split("?")[0] || url;
}

export function ebnApiPlugin(): Plugin {
  return {
    name: "ados-enterprise-ebn",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-ebn/v1")) return next();
        seed();
        const path = pathOnly(url);
        const method = req.method || "GET";

        if (path.endsWith("/health") && method === "GET") {
          return sendJson(res, 200, {
            status: "ok",
            version: "29.0",
            service: "enterprise-ebn",
            mode: "local_vite",
          });
        }

        if (path.endsWith("/inventory") && method === "GET") {
          return sendJson(res, 200, {
            version: "29.0",
            profiles: profiles.size,
            relationships: relationships.size,
            endpoints: [
              "GET /health",
              "GET /profiles",
              "GET /relationships",
              "POST /relationships",
              "GET /graph",
              "GET /city/:id",
              "GET /inventory",
            ],
          });
        }

        if (path.endsWith("/profiles") && method === "GET") {
          return sendJson(res, 200, { profiles: [...profiles.values()] });
        }

        const profileMatch = path.match(/\/profiles\/([^/]+)$/);
        if (profileMatch && method === "GET") {
          const p = profiles.get(decodeURIComponent(profileMatch[1]!));
          if (!p) return sendJson(res, 404, { error: "not_found" });
          return sendJson(res, 200, { profile: p });
        }

        if (path.endsWith("/relationships") && method === "GET") {
          return sendJson(res, 200, { relationships: [...relationships.values()] });
        }

        if (path.endsWith("/relationships") && method === "POST") {
          try {
            const body = JSON.parse((await readBody(req)) || "{}") as {
              fromProfileId?: string;
              toProfileId?: string;
              type?: string;
            };
            if (!body.fromProfileId || !body.toProfileId) {
              return sendJson(res, 400, { error: "from_to_required" });
            }
            const id = `rel_${Math.random().toString(36).slice(2, 8)}`;
            const relationship: Relationship = {
              id,
              fromProfileId: body.fromProfileId,
              toProfileId: body.toProfileId,
              type: body.type || "partner",
              state: "pending",
            };
            relationships.set(id, relationship);
            return sendJson(res, 201, { ok: true, relationship });
          } catch {
            return sendJson(res, 400, { error: "invalid_json" });
          }
        }

        const approveMatch = path.match(/\/relationships\/([^/]+)\/approve$/);
        if (approveMatch && method === "POST") {
          const id = decodeURIComponent(approveMatch[1]!);
          const r = relationships.get(id);
          if (!r) return sendJson(res, 404, { error: "not_found" });
          const next = { ...r, state: "approved" };
          relationships.set(id, next);
          return sendJson(res, 200, { relationship: next });
        }

        if (path.endsWith("/graph") && method === "GET") {
          const nodes = [...profiles.values()].map((p) => ({
            id: p.id,
            profileId: p.id,
            label: p.companyName,
            category: p.category,
            trustLevel: p.trustLevel,
          }));
          const edges = [...relationships.values()].map((r) => ({
            id: `e_${r.id}`,
            relationshipId: r.id,
            from: r.fromProfileId,
            to: r.toProfileId,
            type: r.type,
            state: r.state,
            weight: r.state === "approved" ? 0.8 : 0.2,
          }));
          return sendJson(res, 200, { nodes, edges });
        }

        const cityMatch = path.match(/\/city\/([^/]+)$/);
        if (cityMatch && method === "GET") {
          const id = decodeURIComponent(cityMatch[1]!);
          const p = profiles.get(id);
          if (!p) return sendJson(res, 404, { error: "not_found" });
          const relationshipCount = [...relationships.values()].filter(
            (r) =>
              (r.fromProfileId === id || r.toProfileId === id) && r.state === "approved",
          ).length;
          return sendJson(res, 200, {
            facade: {
              profileId: p.id,
              companyName: p.companyName,
              status: p.status,
              trustLevel: p.trustLevel,
              relationshipCount,
              headquarters: p.headquarters,
              verificationStatus: p.verificationStatus,
              reputationScore: Math.min(100, Math.round(p.trustLevel * 0.7 + relationshipCount * 3)),
            },
          });
        }

        return sendJson(res, 404, { error: "ebn_route_not_found", path });
      });
    },
  };
}
