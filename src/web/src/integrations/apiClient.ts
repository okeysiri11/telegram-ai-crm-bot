/**
 * Identity-aware API client — Sprint 30.4 / refresh in 30.6 / EP-07 timeouts.
 * Reuses authStore session; attaches Authorization; refreshes on 401.
 */

import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { webConfig } from "@/config/webConfig";
import { API_TIMEOUT_MS, prodLog, withTimeoutSignal } from "@/production";

export type IdentityContext = {
  userId: string | null;
  email: string | null;
  tenantId: string | null;
  roleId: string | null;
  organization: string;
  workspaceProject: string;
  permissions: string[];
  accessToken: string | null;
};

export function getIdentityContext(): IdentityContext {
  const auth = useAuthStore.getState();
  const ws = useWorkspaceStore.getState().workspace;
  return {
    userId: auth.user?.id ?? null,
    email: auth.user?.email ?? null,
    tenantId: auth.user?.tenantId ?? null,
    roleId: auth.user?.roleId ?? null,
    organization: ws.company,
    workspaceProject: ws.project,
    permissions: auth.user?.permissions?.length ? auth.user.permissions : ws.permissions,
    accessToken: auth.accessToken,
  };
}

export type ApiFetchInit = RequestInit & {
  anonymous?: boolean;
  skipRefresh?: boolean;
  /** Override default timeout; set 0 to disable. */
  timeoutMs?: number;
};

function buildHeaders(initHeaders: HeadersInit | undefined, anonymous?: boolean): Headers {
  const headers = new Headers(initHeaders || {});
  const ctx = getIdentityContext();
  if (!anonymous && ctx.accessToken) {
    headers.set("Authorization", `Bearer ${ctx.accessToken}`);
  }
  if (ctx.tenantId) headers.set("X-Tenant-Id", ctx.tenantId);
  if (ctx.organization) headers.set("X-Organization", ctx.organization);
  if (ctx.workspaceProject) headers.set("X-Workspace", ctx.workspaceProject);
  if (ctx.roleId) headers.set("X-Role-Id", ctx.roleId);
  // Soft CRM principal role for automotive APIs
  if (!headers.has("X-Platform-Role")) {
    headers.set("X-Platform-Role", "sales_agent");
  }
  return headers;
}

/** Fetch with session + org/workspace context headers when logged in. */
export async function apiFetch(input: string, init: ApiFetchInit = {}): Promise<Response> {
  const { anonymous, skipRefresh, headers: initHeaders, timeoutMs = API_TIMEOUT_MS, signal, ...rest } = init;
  const headers = buildHeaders(initHeaders, anonymous);
  if (!headers.has("Content-Type") && rest.body && typeof rest.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const url = input.startsWith("http") || input.startsWith("/") ? input : `${webConfig.apiBase}/${input}`;
  const timed =
    timeoutMs && timeoutMs > 0
      ? withTimeoutSignal(timeoutMs, signal || undefined)
      : signal;

  let res: Response;
  try {
    res = await fetch(url, { ...rest, headers, signal: timed });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "network_error";
    prodLog("warn", "api_fetch_failed", { url: url.split("?")[0], message: msg });
    throw e;
  }

  if (res.status === 401 && !anonymous && !skipRefresh) {
    const ok = await useAuthStore.getState().refreshSession();
    if (ok) {
      const retryHeaders = buildHeaders(initHeaders, anonymous);
      if (!retryHeaders.has("Content-Type") && rest.body && typeof rest.body === "string") {
        retryHeaders.set("Content-Type", "application/json");
      }
      const retrySignal =
        timeoutMs && timeoutMs > 0 ? withTimeoutSignal(timeoutMs, signal || undefined) : signal;
      res = await fetch(url, { ...rest, headers: retryHeaders, signal: retrySignal });
    }
  }
  return res;
}
