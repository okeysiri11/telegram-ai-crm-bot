/**
 * Identity-aware API client — Sprint 30.4.
 * Reuses authStore session; attaches Authorization for live ISAM/EIC bridge path.
 * Demo tokens are accepted by the shell; production middleware validates real JWTs.
 */

import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { webConfig } from "@/config/webConfig";

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
    permissions: ws.permissions,
    accessToken: auth.accessToken,
  };
}

export type ApiFetchInit = RequestInit & {
  /** Skip Authorization header (health probes, public). */
  anonymous?: boolean;
};

/** Fetch with session + org/workspace context headers when logged in. */
export async function apiFetch(input: string, init: ApiFetchInit = {}): Promise<Response> {
  const { anonymous, headers: initHeaders, ...rest } = init;
  const headers = new Headers(initHeaders || {});
  const ctx = getIdentityContext();

  if (!anonymous && ctx.accessToken) {
    headers.set("Authorization", `Bearer ${ctx.accessToken}`);
  }
  if (ctx.tenantId) headers.set("X-Tenant-Id", ctx.tenantId);
  if (ctx.organization) headers.set("X-Organization", ctx.organization);
  if (ctx.workspaceProject) headers.set("X-Workspace", ctx.workspaceProject);
  if (ctx.roleId) headers.set("X-Role-Id", ctx.roleId);
  if (!headers.has("Content-Type") && rest.body && typeof rest.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const url = input.startsWith("http") || input.startsWith("/") ? input : `${webConfig.apiBase}/${input}`;
  return fetch(url, { ...rest, headers });
}
