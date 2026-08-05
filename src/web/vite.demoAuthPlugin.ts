/**
 * Vite middleware — Sprint 27.1.1 local Demo Authentication API.
 * Serves login when Enterprise backend on :8080 is absent.
 */

import type { Plugin } from "vite";
import type { IncomingMessage, ServerResponse } from "node:http";
import { Buffer } from "node:buffer";

function b64url(obj: unknown): string {
  return Buffer.from(JSON.stringify(obj), "utf8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function mintJwt(claims: Record<string, unknown>): string {
  const now = Math.floor(Date.now() / 1000);
  return [
    b64url({ alg: "HS256", typ: "JWT" }),
    b64url({ iss: "ados-enterprise-local", aud: "enterprise-web-platform", iat: now, exp: now + 43200, ...claims }),
    b64url({ mode: "local", v: 1 }),
  ].join(".");
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

export function demoAuthPlugin(): Plugin {
  return {
    name: "ados-demo-auth",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || "";
        if (!url.startsWith("/api/enterprise-demo-auth/v1")) return next();

        if (url.includes("/health") && req.method === "GET") {
          return sendJson(res, 200, { ok: true, mode: "local_demo", service: "enterprise-demo-auth" });
        }

        if (url.includes("/login") && req.method === "POST") {
          try {
            const raw = await readBody(req);
            const body = JSON.parse(raw || "{}") as {
              email?: string;
              password?: string;
              tenant_id?: string;
              tenantId?: string;
            };
            const email = String(body.email || "").toLowerCase();
            const password = String(body.password || "");
            const tenantId = String(body.tenant_id || body.tenantId || "demo-corp");
            if (password !== "demo" || !email.includes("@")) {
              return sendJson(res, 401, { success: false, error: "Invalid demo credentials" });
            }
            const isOwner = email.includes("owner");
            const identityId = `local_${b64url(email).slice(0, 12)}`;
            const access = mintJwt({ sub: identityId, email, tid: tenantId, role: isOwner ? "platform_owner" : "role_org_owner" });
            const refresh = mintJwt({ sub: identityId, typ: "refresh", tid: tenantId });
            return sendJson(res, 200, {
              success: true,
              data: {
                access_token: access,
                refresh_token: refresh,
                access_expires_at: new Date(Date.now() + 12 * 3600_000).toISOString(),
                session_id: `sess_${Date.now().toString(36)}`,
                principal: {
                  principal_id: identityId,
                  email,
                  tenant_id: tenantId,
                  roles: isOwner ? ["owner", "platform_admin"] : ["employee"],
                  permissions: ["read", "write", "admin"],
                },
              },
            });
          } catch (err) {
            return sendJson(res, 500, { success: false, error: String(err) });
          }
        }

        if (url.includes("/google") && req.method === "POST") {
          try {
            const raw = await readBody(req);
            const body = JSON.parse(raw || "{}") as {
              email?: string;
              name?: string;
              tenant_id?: string;
              tenantId?: string;
            };
            const email = String(body.email || "user@gmail.com").toLowerCase();
            const name = String(body.name || email.split("@")[0] || "Google User");
            const tenantId = String(body.tenant_id || body.tenantId || "demo-corp");
            if (!email.includes("@")) {
              return sendJson(res, 400, { success: false, error: "email required" });
            }
            const identityId = `google_${b64url(email).slice(0, 12)}`;
            const access = mintJwt({
              sub: identityId,
              email,
              tid: tenantId,
              role: "employee",
              provider: "google",
            });
            const refresh = mintJwt({ sub: identityId, typ: "refresh", tid: tenantId });
            const idToken = `google_demo_${JSON.stringify({ email, name, sub: identityId })}`;
            return sendJson(res, 200, {
              success: true,
              data: {
                id_token: idToken,
                access_token: access,
                refresh_token: refresh,
                access_expires_at: new Date(Date.now() + 12 * 3600_000).toISOString(),
                session_id: `sess_g_${Date.now().toString(36)}`,
                principal: {
                  principal_id: identityId,
                  email,
                  name,
                  tenant_id: tenantId,
                  roles: ["employee"],
                  permissions: ["read", "write"],
                  provider: "google",
                },
              },
            });
          } catch (err) {
            return sendJson(res, 500, { success: false, error: String(err) });
          }
        }

        return sendJson(res, 404, { success: false, error: "Not found" });
      });
    },
  };
}
