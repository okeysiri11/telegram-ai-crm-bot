/**
 * Sprint 27.1.1 — Local Demo Authentication Provider.
 * Used when Enterprise ISAM / platform IAM are unreachable (typical: Vite proxy → :8080 down).
 * Mints a real JWT-shaped token (no legacy `.demo` suffix) and persists via authStore.
 *
 * Production builds never activate this bypass, even if VITE_DEMO_AUTH=true.
 */

import type { AuthSessionPayload } from "./identityApi";
import { isGlobeFlyEmail, globeFlyUserByEmail } from "@/demo/globefly";
import { demoUserByEmail, isMultiRoleDemoEmail } from "@/multi-role/demoUsers";
import { saveFirstEntry } from "@/onboarding/firstEntryStore";

/** Existing DEV password — override locally via VITE_DEMO_OWNER_PASSWORD (not for production). */
export const DEMO_PASSWORD =
  (typeof import.meta !== "undefined" &&
    typeof import.meta.env?.VITE_DEMO_OWNER_PASSWORD === "string" &&
    import.meta.env.VITE_DEMO_OWNER_PASSWORD.trim()) ||
  "demo";
export const OWNER_DEMO_EMAIL = "owner@ados.demo";
export const OWNER_DEMO_TENANT = "ados";

export const OWNER_PERMISSIONS = [
  "read",
  "write",
  "admin",
  "super_admin",
  "all",
  "crm",
  "erp",
  "finance",
  "builder",
  "hr",
  "legal",
  "recruiting",
  "crypto",
  "agro",
  "beauty",
  "cafe",
  "drone",
  "travel",
  "marketing",
  "command_center",
  "settings",
  "organizations",
  "workspaces",
  "developer",
  "documents",
  "knowledge",
] as const;

export type DemoAuthEnv = {
  PROD?: boolean;
  DEV?: boolean;
  VITE_DEMO_AUTH?: string;
};

/** Pure policy — production builds cannot silently enable demo bypass. */
export function resolveDemoAuthEnabled(env: DemoAuthEnv): boolean {
  if (env.PROD) {
    if (env.VITE_DEMO_AUTH === "true") {
      console.error(
        "[ADOS] VITE_DEMO_AUTH=true is ignored in production builds. Demo auth bypass is disabled.",
      );
    }
    return false;
  }
  if (env.VITE_DEMO_AUTH === "false") return false;
  if (env.VITE_DEMO_AUTH === "true") return true;
  return Boolean(env.DEV);
}

export function isDemoAuthEnabled(): boolean {
  return resolveDemoAuthEnabled({
    PROD: Boolean(import.meta.env.PROD),
    DEV: Boolean(import.meta.env.DEV),
    VITE_DEMO_AUTH: import.meta.env.VITE_DEMO_AUTH as string | undefined,
  });
}

/** Local Owner one-click surface: DEV only. Production builds always false. */
export function isLocalOwnerLoginEnabled(): boolean {
  if (import.meta.env.PROD) return false;
  return isDemoAuthEnabled();
}

export function assertLocalOwnerLoginAllowed(): void {
  if (import.meta.env.PROD || !isDemoAuthEnabled()) {
    throw new Error("Local Owner login is DEV-only and is disabled in production.");
  }
}

/** Canonical in-process Owner session. Never calls ISAM, Google, or the API. */
export function loginAsCanonicalOwner(): AuthSessionPayload {
  assertLocalOwnerLoginAllowed();
  return loginViaDemoAuth(OWNER_DEMO_EMAIL, DEMO_PASSWORD, OWNER_DEMO_TENANT);
}

export function isDemoOwnerEmail(email: string): boolean {
  return email.trim().toLowerCase() === OWNER_DEMO_EMAIL;
}

/** Google OAuth is optional; hide the button unless a client id is configured. */
export function isGoogleAuthConfigured(): boolean {
  const id = String(
    (typeof import.meta !== "undefined" &&
      (import.meta.env?.VITE_GOOGLE_CLIENT_ID || import.meta.env?.GOOGLE_CLIENT_ID)) ||
      "",
  ).trim();
  return id.length > 0;
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
    isMultiRoleDemoEmail(lower) ||
    lower.endsWith("@demo.corp") ||
    lower.endsWith("@local.dev") ||
    lower.endsWith("@globefly.demo") ||
    lower.endsWith("@ados.demo") ||
    lower === OWNER_DEMO_EMAIL ||
    lower === "ops@demo.corp"
  );
}

function completeOwnerFirstEntry(tenantId: string) {
  try {
    saveFirstEntry({
      completed: true,
      step: "dashboard",
      roleId: "platform_owner",
      companyName: "ADOS Platform",
      language: "ru",
      workspaceId: `ws_${tenantId}`,
    });
  } catch {
    /* tests without a full first-entry catalog still log in */
  }
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
    throw new Error(`Local demo auth rejected. Try ${OWNER_DEMO_EMAIL}.`);
  }

  const multi = demoUserByEmail(email);
  const gf = globeFlyUserByEmail(email);
  const canonicalOwner = isDemoOwnerEmail(email);
  const owner =
    canonicalOwner ||
    email.toLowerCase().includes("owner") ||
    multi?.viewMode === "platform_owner" ||
    gf?.defaultViewMode === "platform_owner";
  const isClient =
    !owner &&
    (multi?.viewMode === "client" ||
      gf?.defaultViewMode === "client" ||
      email.toLowerCase().startsWith("client@") ||
      email.toLowerCase().startsWith("travel@") ||
      email.toLowerCase().startsWith("build@") ||
      email.toLowerCase().startsWith("legal@") ||
      email.toLowerCase().startsWith("seller@"));
  const roleId = isClient
    ? "client"
    : owner
      ? "platform_owner"
      : multi?.roleIds[0] || gf?.roleIds[0] || "role_org_owner";
  const roles = owner
    ? ["owner", "platform_owner", "company_owner", "platform_admin", "super_admin"]
    : multi?.roleIds ||
      gf?.roleIds ||
      ["employee", "manager"];
  const resolvedTenant = canonicalOwner
    ? OWNER_DEMO_TENANT
    : multi?.tenantId || (isGlobeFlyEmail(email) ? "globefly" : tenantId || OWNER_DEMO_TENANT);
  const identityId = `local_${b64url(email.toLowerCase()).slice(0, 16)}`;
  const sessionId = `sess_${Date.now().toString(36)}`;
  const permissions = owner
    ? [...OWNER_PERMISSIONS]
    : isClient
      ? ["read", "write", "crm", "documents"]
      : ["read", "write", "admin", "crm", "erp", "finance", "builder"];

  const accessToken = mintLocalDemoJwt({
    sub: identityId,
    email,
    tid: resolvedTenant,
    role: roleId,
    roles,
    permissions,
  });
  const refreshToken = mintLocalDemoJwt({
    sub: identityId,
    typ: "refresh",
    tid: resolvedTenant,
    email,
  });

  if (owner) completeOwnerFirstEntry(resolvedTenant);

  return {
    user: {
      id: identityId,
      email: email.trim().toLowerCase(),
      name: multi?.name || gf?.name || (owner ? "Platform Owner" : email.split("@")[0] || "demo"),
      tenantId: resolvedTenant,
      roleId,
      identityId,
      sessionId,
      permissions,
      roles,
    },
    accessToken,
    refreshToken,
    accessExpiresAt: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
    authMode: "platform_jwt",
  };
}

/** Demo-mode Google: local session, no OAuth, no ISAM. */
export function loginViaDemoGoogle(
  email: string,
  name: string,
  tenantId: string,
): AuthSessionPayload {
  const normalized = (email || OWNER_DEMO_EMAIL).trim().toLowerCase();
  if (isDemoOwnerEmail(normalized) || normalized.endsWith("@demo.corp") || normalized.includes("owner")) {
    return loginViaDemoAuth(normalized.includes("@") ? normalized : OWNER_DEMO_EMAIL, DEMO_PASSWORD, tenantId);
  }
  const session = loginViaDemoAuth(OWNER_DEMO_EMAIL, DEMO_PASSWORD, tenantId);
  return {
    ...session,
    user: {
      ...session.user,
      email: normalized.includes("@") ? normalized : session.user.email,
      name: name || session.user.name,
    },
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
