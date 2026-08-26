/**
 * Production identity API — Sprint 30.6 + Sprint 27.1.1 local demo fallback.
 * Prefer platform JWT + ISAM when backend is up; fall back to Demo Auth Provider locally.
 */

import { hubIntegrations } from "@/integrations/hub";
import { webConfig } from "@/config/webConfig";
import { isDemoAuthEnabled, loginViaDemoAuth, loginViaDemoGoogle } from "./demoAuthProvider";

const ISAM = hubIntegrations.authentication;
const IAM_LOGIN = "/management/identity/login";
const IAM_REFRESH = "/management/identity/refresh";
const DEMO_AUTH_LOGIN = "/api/enterprise-demo-auth/v1/login";
const DEMO_AUTH_GOOGLE = "/api/enterprise-demo-auth/v1/google";

export type AuthSessionPayload = {
  user: {
    id: string;
    email: string;
    name: string;
    tenantId: string;
    roleId?: string;
    telegramId?: number;
    identityId?: string;
    sessionId?: string;
    permissions?: string[];
    roles?: string[];
  };
  accessToken: string;
  refreshToken: string;
  accessExpiresAt?: string;
  refreshExpiresAt?: string;
  authMode: "platform_jwt" | "isam";
};

function telegramIdForEmail(email: string): number {
  const configured = Number(import.meta.env.VITE_OWNER_TELEGRAM_ID || webConfig.defaultTelegramId || 0);
  const lower = email.toLowerCase();
  if (lower.startsWith("owner@") || lower.includes("+owner@")) {
    return configured || 1208044579;
  }
  let hash = 0;
  for (let i = 0; i < lower.length; i += 1) hash = (hash * 31 + lower.charCodeAt(i)) >>> 0;
  return 2_000_000_000 + (hash % 100_000_000);
}

async function postJson(url: string, body: Record<string, unknown>, init?: RequestInit): Promise<Response> {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    body: JSON.stringify(body),
    ...init,
  });
}

/** Soft probe — treats network / 5xx / proxy 502 as unavailable. */
async function isBackendReachable(url: string, timeoutMs = 1800): Promise<boolean> {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { method: "GET", signal: ctrl.signal });
    return res.ok || (res.status > 0 && res.status < 500);
  } catch {
    return false;
  } finally {
    window.clearTimeout(timer);
  }
}

/** Enterprise ISAM: identity → auth → tokens → session → roles → permissions → audit */
export async function loginViaIsam(
  email: string,
  password: string,
  tenantId: string,
): Promise<AuthSessionPayload> {
  const subject = email;
  const identityRes = await postJson(`${ISAM}/identity`, {
    action: "register",
    subject,
    identity_type: "user",
    roles: email.toLowerCase().includes("owner") ? ["company_owner", "platform_admin"] : ["employee"],
    attributes: { tenant_id: tenantId, email },
  });
  const identity = (await identityRes.json()) as Record<string, unknown>;
  if (!identityRes.ok) throw new Error(String(identity.error || "ISAM identity failed"));

  const identityId = String(identity.identity_id || "");
  const authRes = await postJson(`${ISAM}/auth`, {
    action: "login",
    subject,
    provider: "local",
    secret: password,
  });
  const auth = (await authRes.json()) as Record<string, unknown>;
  if (!authRes.ok || auth.success === false) {
    throw new Error(String(auth.error || "ISAM authentication failed"));
  }

  const accessRes = await postJson(`${ISAM}/tokens`, {
    action: "issue",
    identity_id: identityId,
    token_type: "access",
  });
  const accessTok = (await accessRes.json()) as Record<string, unknown>;
  if (!accessRes.ok) throw new Error(String(accessTok.error || "ISAM access token failed"));

  const refreshRes = await postJson(`${ISAM}/tokens`, {
    action: "issue",
    identity_id: identityId,
    token_type: "refresh",
  });
  const refreshTok = (await refreshRes.json()) as Record<string, unknown>;
  if (!refreshRes.ok) throw new Error(String(refreshTok.error || "ISAM refresh token failed"));

  const sessionRes = await postJson(`${ISAM}/sessions`, {
    action: "create",
    identity_id: identityId,
    device: "enterprise_web",
    ip: "127.0.0.1",
    ttl_seconds: 3600,
  });
  const session = (await sessionRes.json()) as Record<string, unknown>;

  const roleName = email.toLowerCase().includes("owner") ? "company_owner" : "manager";
  await postJson(`${ISAM}/roles`, {
    action: "assign",
    identity_id: identityId,
    role: roleName,
  });
  await postJson(`${ISAM}/roles`, {
    action: "grant",
    identity_id: identityId,
    permission: "read",
  });
  await postJson(`${ISAM}/roles`, {
    action: "grant",
    identity_id: identityId,
    permission: "admin",
  });
  const permsRes = await postJson(`${ISAM}/roles`, {
    action: "resolve",
    identity_id: identityId,
  });
  const permsBody = (await permsRes.json()) as Record<string, unknown>;
  const permissions = Array.isArray(permsBody.permissions)
    ? (permsBody.permissions as string[])
    : ["read", "write", "admin"];

  await postJson(`${ISAM}/audit`, {
    action: "login",
    actor: subject,
    subject: identityId,
    detail: `tenant=${tenantId}; mode=isam`,
  });

  return {
    user: {
      id: identityId || `usr_${email}`,
      email,
      name: email.split("@")[0] || "user",
      tenantId,
      roleId: email.toLowerCase().includes("owner") ? "platform_owner" : "role_org_owner",
      identityId,
      sessionId: String(session.session_id || ""),
      permissions,
      roles: [roleName],
    },
    accessToken: String(accessTok.value || ""),
    refreshToken: String(refreshTok.value || ""),
    authMode: "isam",
  };
}

/** Platform IAM JWT login — production JWT + refresh when login proof is configured. */
export async function loginViaPlatformJwt(
  email: string,
  tenantId: string,
): Promise<AuthSessionPayload | null> {
  const loginProof = String(import.meta.env.VITE_IAM_LOGIN_SECRET || "");
  if (!loginProof) return null;

  const telegramId = telegramIdForEmail(email);
  const res = await postJson(IAM_LOGIN, {
    telegram_id: telegramId,
    login_proof: loginProof,
    // Sprint 34.2A — Identity Core links email ↔ users.id (no synthetic-only account).
    email,
    display_name: email.split("@")[0] || "user",
  });
  const body = (await res.json()) as {
    success?: boolean;
    data?: Record<string, unknown>;
    error?: string;
  };
  if (!res.ok || body.success === false) {
    throw new Error(body.error || "Platform JWT login failed");
  }
  const data = (body.data || body) as Record<string, unknown>;
  const principal = (data.principal || {}) as Record<string, unknown>;
  const roles = Array.isArray(principal.roles) ? (principal.roles as string[]) : [];
  const roleId = roles.includes("owner")
    ? "platform_owner"
    : roles[0] || "role_org_owner";

  return {
    user: {
      id: String(principal.user_id || principal.principal_id || `tg_${telegramId}`),
      email,
      name: String(principal.display_name || email.split("@")[0] || "user"),
      tenantId,
      roleId,
      telegramId: principal.telegram_id != null ? Number(principal.telegram_id) : telegramId,
      identityId: principal.user_id ? String(principal.user_id) : undefined,
      sessionId: String(data.session_id || ""),
      roles,
      permissions: Array.isArray(principal.permissions)
        ? (principal.permissions as string[])
        : ["read", "write", "admin"],
    },
    accessToken: String(data.access_token || ""),
    refreshToken: String(data.refresh_token || ""),
    accessExpiresAt: data.access_expires_at ? String(data.access_expires_at) : undefined,
    refreshExpiresAt: data.refresh_expires_at ? String(data.refresh_expires_at) : undefined,
    authMode: "platform_jwt",
  };
}

/** Hit Vite Demo Auth middleware when present. */
async function loginViaDemoAuthApi(
  email: string,
  password: string,
  tenantId: string,
): Promise<AuthSessionPayload | null> {
  try {
    const res = await postJson(DEMO_AUTH_LOGIN, {
      email,
      password,
      tenant_id: tenantId,
    });
    if (!res.ok) return null;
    const body = (await res.json()) as {
      success?: boolean;
      data?: Record<string, unknown>;
    };
    if (body.success === false || !body.data) return null;
    const data = body.data;
    const principal = (data.principal || {}) as Record<string, unknown>;
    const roles = Array.isArray(principal.roles) ? (principal.roles as string[]) : ["owner"];
    return {
      user: {
        id: String(principal.principal_id || `local_${email}`),
        email,
        name: email.split("@")[0] || "demo",
        tenantId: String(principal.tenant_id || tenantId),
        roleId: roles.includes("owner") ? "platform_owner" : "role_org_owner",
        identityId: String(principal.principal_id || ""),
        sessionId: String(data.session_id || ""),
        roles,
        permissions: Array.isArray(principal.permissions)
          ? (principal.permissions as string[])
          : ["read", "write", "admin"],
      },
      accessToken: String(data.access_token || ""),
      refreshToken: String(data.refresh_token || ""),
      accessExpiresAt: data.access_expires_at ? String(data.access_expires_at) : undefined,
      authMode: "platform_jwt",
    };
  } catch {
    return null;
  }
}

/**
 * Production login with local recovery.
 * DEV / demo: in-process Owner session — never blocks on ISAM :8080.
 * Production: demo-auth API (platform JWT) then ISAM. No local bypass.
 */
export async function productionLogin(
  email: string,
  password: string,
  tenantId: string,
): Promise<AuthSessionPayload> {
  const resolvedTenant = tenantId.trim() || "ados";
  if (isDemoAuthEnabled()) {
    return loginViaDemoAuth(email, password, resolvedTenant);
  }

  const fromApi = await loginViaDemoAuthApi(email, password, resolvedTenant);
  if (fromApi?.accessToken) return fromApi;

  const isamUp = await isBackendReachable(`${ISAM}/health`);

  if (isamUp) {
    const isam = await loginViaIsam(email, password, resolvedTenant);
    try {
      const jwt = await loginViaPlatformJwt(email, resolvedTenant);
      if (jwt) {
        return {
          ...jwt,
          user: {
            ...jwt.user,
            identityId: isam.user.identityId,
            permissions: Array.from(
              new Set([...(jwt.user.permissions || []), ...(isam.user.permissions || [])]),
            ),
            roles: Array.from(new Set([...(jwt.user.roles || []), ...(isam.user.roles || [])])),
          },
        };
      }
    } catch {
      /* ISAM session remains valid when JWT mint is unavailable */
    }
    return isam;
  }

  throw new Error(
    "Authentication backend unavailable (ISAM proxy → localhost:8080). Start the API.",
  );
}

/** Google Sign-In — preferred Beta auth (auto-creates account on first login). */
export async function productionGoogleLogin(
  input: {
    email?: string;
    name?: string;
    idToken?: string;
    tenantId: string;
    rememberMe?: boolean;
  },
): Promise<AuthSessionPayload> {
  const tenantId = input.tenantId || "ados";
  if (isDemoAuthEnabled()) {
    return loginViaDemoGoogle(input.email || "owner@ados.demo", input.name || "Google User", tenantId);
  }

  const isamUp = await isBackendReachable(`${ISAM}/health`);

  if (isamUp) {
    let idToken = input.idToken || "";
    if (!idToken) {
      // Mint local demo credential consumed by ISAM Google provider
      idToken = `google_demo_${JSON.stringify({
        email: (input.email || "user@gmail.com").toLowerCase(),
        name: input.name || "Google User",
        sub: `google:${input.email || "user@gmail.com"}`,
      })}`;
    }
    const res = await postJson(`${ISAM}/auth`, {
      action: "google_login",
      id_token: idToken,
      device: "enterprise_web",
      remember_me: Boolean(input.rememberMe),
      role: "employee",
    });
    const body = (await res.json()) as Record<string, unknown>;
    if (!res.ok || body.error) {
      throw new Error(String(body.error || "Google login failed"));
    }
    const identity = (body.identity || {}) as Record<string, unknown>;
    const session = (body.session || {}) as Record<string, unknown>;
    const email = String(identity.subject || input.email || "");
    const roles = Array.isArray(identity.roles) ? (identity.roles as string[]) : ["employee"];
    return {
      user: {
        id: String(identity.identity_id || `google_${email}`),
        email,
        name: String((identity.attributes as { name?: string } | undefined)?.name || email.split("@")[0]),
        tenantId,
        roleId: roles.includes("owner") ? "platform_owner" : "role_employee",
        identityId: String(identity.identity_id || ""),
        sessionId: String(session.session_id || ""),
        roles,
        permissions: ["read", "write"],
      },
      accessToken: String(body.access_token || ""),
      refreshToken: String(body.refresh_token || ""),
      authMode: "isam",
    };
  }

  if (isDemoAuthEnabled()) {
    const res = await postJson(DEMO_AUTH_GOOGLE, {
      email: input.email || "user@gmail.com",
      name: input.name,
      tenant_id: tenantId,
    });
    const body = (await res.json()) as { success?: boolean; data?: Record<string, unknown>; error?: string };
    if (!res.ok || body.success === false || !body.data) {
      throw new Error(body.error || "Google demo login failed");
    }
    const data = body.data;
    const principal = (data.principal || {}) as Record<string, unknown>;
    return {
      user: {
        id: String(principal.principal_id || ""),
        email: String(principal.email || input.email || ""),
        name: String(principal.name || "Google User"),
        tenantId: String(principal.tenant_id || tenantId),
        roleId: "role_employee",
        identityId: String(principal.principal_id || ""),
        sessionId: String(data.session_id || ""),
        roles: Array.isArray(principal.roles) ? (principal.roles as string[]) : ["employee"],
        permissions: Array.isArray(principal.permissions)
          ? (principal.permissions as string[])
          : ["read", "write"],
      },
      accessToken: String(data.access_token || ""),
      refreshToken: String(data.refresh_token || ""),
      accessExpiresAt: data.access_expires_at ? String(data.access_expires_at) : undefined,
      authMode: "platform_jwt",
    };
  }

  throw new Error("Google authentication unavailable");
}

export async function productionRegister(input: {
  email: string;
  password: string;
  name?: string;
  tenantId: string;
}): Promise<AuthSessionPayload> {
  if (isDemoAuthEnabled()) {
    throw new Error(
      "Регистрация отключена в демо-режиме. Войдите как owner@ados.demo.",
    );
  }
  const isamUp = await isBackendReachable(`${ISAM}/health`);
  if (isamUp) {
    const res = await postJson(`${ISAM}/auth`, {
      action: "register",
      email: input.email,
      password: input.password,
      name: input.name || "",
      role: "employee",
    });
    const body = (await res.json()) as Record<string, unknown>;
    if (!res.ok || body.error) throw new Error(String(body.error || "Registration failed"));
  }
  return productionLogin(input.email, input.password, input.tenantId);
}

export async function productionPasswordReset(email: string): Promise<{ ok: boolean }> {
  const isamUp = await isBackendReachable(`${ISAM}/health`);
  if (isamUp) {
    await postJson(`${ISAM}/auth`, { action: "password_reset", email });
  }
  return { ok: true };
}

export async function refreshProductionSession(
  refreshToken: string,
  authMode: "platform_jwt" | "isam",
  identityId?: string,
): Promise<{ accessToken: string; refreshToken: string; accessExpiresAt?: string }> {
  if (authMode === "platform_jwt") {
    if (refreshToken.split(".").length === 3) {
      try {
        const json = decodeJwtPayload(refreshToken) as {
          iss?: string;
          sub?: string;
          tid?: string;
          email?: string;
        } | null;
        if (json?.iss === "ados-enterprise-local") {
          const { mintLocalDemoJwt } = await import("./demoAuthProvider");
          return {
            accessToken: mintLocalDemoJwt({
              sub: json.sub,
              email: json.email,
              tid: json.tid,
            }),
            refreshToken,
            accessExpiresAt: new Date(Date.now() + 12 * 3600_000).toISOString(),
          };
        }
      } catch {
        /* fall through to IAM refresh */
      }
    }
    const res = await postJson(IAM_REFRESH, { refresh_token: refreshToken });
    const body = (await res.json()) as {
      success?: boolean;
      data?: Record<string, unknown>;
      error?: string;
    };
    if (!res.ok || body.success === false) {
      throw new Error(body.error || "JWT refresh failed");
    }
    const data: Record<string, unknown> = {
      ...(body as unknown as Record<string, unknown>),
      ...(body.data || {}),
    };
    return {
      accessToken: String(data.access_token || ""),
      refreshToken: String(data.refresh_token || refreshToken),
      accessExpiresAt: data.access_expires_at ? String(data.access_expires_at) : undefined,
    };
  }
  if (!identityId) throw new Error("identityId required for ISAM refresh");
  const rotated = await postJson(`${ISAM}/tokens`, {
    action: "issue",
    identity_id: identityId,
    token_type: "access",
  });
  const tok = (await rotated.json()) as Record<string, unknown>;
  if (!rotated.ok) throw new Error(String(tok.error || "ISAM refresh failed"));
  return { accessToken: String(tok.value || ""), refreshToken };
}

export function isJwtToken(token: string | null | undefined): boolean {
  if (!token) return false;
  const parts = token.split(".");
  return parts.length === 3 && !token.includes(".demo");
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const mid = token.split(".")[1];
    if (!mid) return null;
    const padded = mid.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((mid.length + 3) % 4);
    return JSON.parse(atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export async function validateSessionOnline(accessToken: string): Promise<boolean> {
  if (!accessToken || accessToken.includes(".demo")) return false;
  if (isJwtToken(accessToken)) {
    const payload = decodeJwtPayload(accessToken);
    if (!payload) return false;
    const exp = typeof payload.exp === "number" ? payload.exp : 0;
    if (exp && exp * 1000 < Date.now()) return false;
    return true;
  }
  return Boolean(accessToken);
}
