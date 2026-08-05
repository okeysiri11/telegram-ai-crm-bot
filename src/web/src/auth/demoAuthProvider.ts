/**
 * Sprint 27.1.1 — Local Demo Authentication Provider.
 * Used when Enterprise ISAM / platform IAM are unreachable (typical: Vite proxy → :8080 down).
 * Mints a real JWT-shaped token (no legacy `.demo` suffix) and persists via authStore.
 */

import type { AuthSessionPayload } from "./identityApi";

const DEMO_PASSWORD = "demo";

export function isDemoAuthEnabled(): boolean {
  if (import.meta.env.VITE_DEMO_AUTH === "false") return false;
  if (import.meta.env.VITE_DEMO_AUTH === "true") return true;
  return Boolean(import.meta.env.DEV);
}

function b64url(value: unknown): string {
  const json = typeof value === "string" ? value : JSON.stringify(value);
  const bytes = new TextEncoder().encode(json);
  let bin = "";
  bytes.forEach((b) => {
    bin += String.fromCharCode(b);
  });
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

/** HS256-shaped local JWT — signature is local-only (not verified server-side). */
export function mintLocalDemoJwt(claims: Record<string, unknown>): string {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url({ alg: "HS256", typ: "JWT" });
  const payload = b64url({
    iss: "ados-enterprise-local",
    aud: "enterprise-web-platform",
    iat: now,
    exp: now + 60 * 60 * 12,
    ...claims,
  });
  const signature = b64url({ mode: "local", v: 1 });
  return `${header}.${payload}.${signature}`;
}

function acceptDemoCredentials(email: string, password: string): boolean {
  if (password !== DEMO_PASSWORD) return false;
  const lower = email.toLowerCase();
  return (
    lower.endsWith("@demo.corp") ||
    lower.endsWith("@local.dev") ||
    lower === "owner@demo.corp" ||
    lower === "ops@demo.corp"
  );
}

/**
 * Create a local session for demo users when backend IAM is unavailable.
 */
export function loginViaDemoAuth(
  email: string,
  password: string,
  tenantId: string,
): AuthSessionPayload {
  if (!acceptDemoCredentials(email, password)) {
    throw new Error(
      "Local demo auth rejected credentials. Use owner@demo.corp / demo (tenant demo-corp).",
    );
  }

  const isOwner = email.toLowerCase().includes("owner");
  const roleId = isOwner ? "platform_owner" : "role_org_owner";
  const roles = isOwner ? ["owner", "company_owner", "platform_admin"] : ["employee", "manager"];
  const identityId = `local_${b64url(email.toLowerCase()).slice(0, 16)}`;
  const sessionId = `sess_${Date.now().toString(36)}`;

  const accessToken = mintLocalDemoJwt({
    sub: identityId,
    email,
    tid: tenantId,
    role: roleId,
    roles,
  });
  const refreshToken = mintLocalDemoJwt({
    sub: identityId,
    typ: "refresh",
    tid: tenantId,
  });

  return {
    user: {
      id: identityId,
      email,
      name: email.split("@")[0] || "demo",
      tenantId,
      roleId,
      identityId,
      sessionId,
      permissions: ["read", "write", "admin", "crm", "erp", "finance", "builder"],
      roles,
    },
    accessToken,
    refreshToken,
    accessExpiresAt: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
    authMode: "platform_jwt",
  };
}

export function isLocalDemoToken(token: string | null | undefined): boolean {
  if (!token || token.split(".").length !== 3) return false;
  try {
    const mid = token.split(".")[1]!;
    const padded = mid.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((mid.length + 3) % 4);
    const json = atob(padded);
    return json.includes("ados-enterprise-local");
  } catch {
    return false;
  }
}
