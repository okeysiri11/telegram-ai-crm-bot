/**
 * Remote / multi-tenant command policy — Sprint 28.7.
 * Scopes: user · organization · workspace · device · remote_session
 */

import { useAuthStore } from "@/auth/authStore";
import type {
  CommandDefinition,
  CommandExecutionContext,
  CommandPolicyContext,
  PolicyScope,
} from "./commandTypes";

let scope: PolicyScope = "user";
let deviceId =
  typeof window !== "undefined"
    ? localStorage.getItem("ews_device_id_v1") ||
      (() => {
        const id = `dev_${Math.random().toString(36).slice(2, 12)}`;
        try {
          localStorage.setItem("ews_device_id_v1", id);
        } catch {
          /* ignore */
        }
        return id;
      })()
    : "server";
let remoteSessionId: string | null = null;
let workspaceOverride: string | null = null;

export const commandPolicy = {
  setScope(next: PolicyScope) {
    scope = next;
  },

  getScope(): PolicyScope {
    return scope;
  },

  setRemoteSession(id: string | null) {
    remoteSessionId = id;
  },

  setWorkspace(id: string | null) {
    workspaceOverride = id;
  },

  buildContext(partial?: Partial<CommandPolicyContext>): CommandPolicyContext {
    const user = useAuthStore.getState().user;
    return {
      scope,
      userId: user?.id || null,
      organizationId: user?.tenantId || null,
      workspaceId: workspaceOverride || user?.tenantId || "default",
      deviceId,
      remoteSessionId,
      tenantId: user?.tenantId || null,
      ...partial,
    };
  },

  /**
   * Evaluate whether a command may run in the current policy scope.
   * Future: remote policy service. Local rules are multi-tenant ready.
   */
  evaluate(
    def: CommandDefinition,
    ctx: CommandExecutionContext,
  ): { allowed: boolean; reason?: string; policy: CommandPolicyContext } {
    const policy = ctx.policy || this.buildContext();
    const allowedScopes = def.policyScopes || (["user", "organization", "workspace", "device", "remote_session"] as PolicyScope[]);

    if (!allowedScopes.includes(policy.scope)) {
      return {
        allowed: false,
        reason: `scope_denied:${policy.scope}`,
        policy,
      };
    }

    if (policy.scope === "remote_session" && !policy.remoteSessionId) {
      return { allowed: false, reason: "remote_session_required", policy };
    }

    if (policy.scope === "organization" && !policy.organizationId) {
      return { allowed: false, reason: "organization_required", policy };
    }

    // Tenant isolation stub — deny if explicit tenant mismatch in args
    const argTenant = ctx.args.tenantId;
    if (typeof argTenant === "string" && policy.tenantId && argTenant !== policy.tenantId) {
      return { allowed: false, reason: "tenant_mismatch", policy };
    }

    return { allowed: true, policy };
  },
};
