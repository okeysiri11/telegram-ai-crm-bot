import type { McpPermissionLevel } from "./types.js";
import type { MCPConfig } from "./MCPConfig.js";
import { MCPPermissions } from "./MCPPermissions.js";

export interface AuthResult {
  readonly ok: boolean;
  readonly token: string | null;
  readonly permission: McpPermissionLevel;
  readonly reason?: string;
}

/**
 * Session token authentication + runtime/permission validation hooks.
 */
export class MCPAuthentication {
  private readonly tokens = new Map<
    string,
    { permission: McpPermissionLevel; label: string; createdAt: string }
  >();
  private readonly permissions = new MCPPermissions();

  constructor(private readonly config: MCPConfig) {
    const cfg = config.get();
    this.tokens.set(cfg.authentication.defaultAdminToken, {
      permission: "admin",
      label: "default-admin",
      createdAt: new Date().toISOString(),
    });
  }

  issueToken(
    permission: McpPermissionLevel,
    label = "session",
  ): { token: string; permission: McpPermissionLevel } {
    const token = `mcp_${permission}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    this.tokens.set(token, {
      permission,
      label,
      createdAt: new Date().toISOString(),
    });
    return { token, permission };
  }

  revokeToken(token: string): boolean {
    return this.tokens.delete(token);
  }

  authenticate(token: string | null | undefined): AuthResult {
    const cfg = this.config.get();
    if (!cfg.authentication.required) {
      return {
        ok: true,
        token: token ?? null,
        permission: cfg.permissions.defaultLevel,
      };
    }
    if (!token) {
      if (cfg.permissions.allowAnonymousRead) {
        return { ok: true, token: null, permission: "read" };
      }
      return {
        ok: false,
        token: null,
        permission: "read",
        reason: "Missing session token",
      };
    }
    const entry = this.tokens.get(token);
    if (!entry) {
      return {
        ok: false,
        token,
        permission: "read",
        reason: "Invalid session token",
      };
    }
    return { ok: true, token, permission: entry.permission };
  }

  /**
   * Runtime validation: token must authenticate; optional provider claim check.
   */
  validateRuntimeAccess(input: {
    token?: string | null;
    required: McpPermissionLevel;
    providerId?: string;
  }): AuthResult & { denied?: boolean } {
    const auth = this.authenticate(input.token);
    if (!auth.ok) return { ...auth, denied: true };
    if (!this.permissions.allows(auth.permission, input.required)) {
      return {
        ok: false,
        token: auth.token,
        permission: auth.permission,
        reason: `Requires ${input.required}`,
        denied: true,
      };
    }
    // Provider validation hook — ensure claimed provider id is non-empty when given
    if (input.providerId !== undefined && !input.providerId.trim()) {
      return {
        ok: false,
        token: auth.token,
        permission: auth.permission,
        reason: "Invalid provider claim",
        denied: true,
      };
    }
    return auth;
  }

  listSessions(): Array<{
    tokenPreview: string;
    permission: McpPermissionLevel;
    label: string;
    createdAt: string;
  }> {
    return [...this.tokens.entries()].map(([token, v]) => ({
      tokenPreview: `${token.slice(0, 12)}…`,
      permission: v.permission,
      label: v.label,
      createdAt: v.createdAt,
    }));
  }
}

export function createMCPAuthentication(config: MCPConfig): MCPAuthentication {
  return new MCPAuthentication(config);
}
