import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import type { McpPermissionLevel, McpTransportKind } from "./types.js";

export interface McpConfigState {
  enabled: boolean;
  host: string;
  port: number;
  transport: McpTransportKind;
  authentication: {
    required: boolean;
    tokenHeader: string;
    defaultAdminToken: string;
  };
  permissions: {
    defaultLevel: McpPermissionLevel;
    allowAnonymousRead: boolean;
  };
  runtime: {
    baseUrl: string;
  };
  logging: {
    connections: boolean;
    toolCalls: boolean;
    permissionFailures: boolean;
    resourceReads: boolean;
    latency: boolean;
  };
}

export const DEFAULT_MCP_CONFIG: McpConfigState = {
  enabled: true,
  host: "127.0.0.1",
  port: 3100,
  transport: "http+stdio",
  authentication: {
    required: true,
    tokenHeader: "x-ados-mcp-token",
    defaultAdminToken: "ados-mcp-dev-token",
  },
  permissions: {
    defaultLevel: "read",
    allowAnonymousRead: false,
  },
  runtime: {
    baseUrl: "http://127.0.0.1:3000",
  },
  logging: {
    connections: true,
    toolCalls: true,
    permissionFailures: true,
    resourceReads: true,
    latency: true,
  },
};

/**
 * Loads config/mcp.config.json with env overrides.
 */
export class MCPConfig {
  private state: McpConfigState;

  constructor(initial?: Partial<McpConfigState>) {
    this.state = mergeConfig(DEFAULT_MCP_CONFIG, initial ?? {});
  }

  static loadFromDisk(cwd = process.cwd()): MCPConfig {
    const candidates = [
      resolve(cwd, "config/mcp.config.json"),
      resolve(cwd, "../config/mcp.config.json"),
      resolve(cwd, "../../config/mcp.config.json"),
    ];
    for (const path of candidates) {
      if (!existsSync(path)) continue;
      try {
        const raw = JSON.parse(readFileSync(path, "utf8")) as Partial<McpConfigState>;
        const cfg = new MCPConfig(raw);
        cfg.applyEnv();
        return cfg;
      } catch {
        /* try next */
      }
    }
    const cfg = new MCPConfig();
    cfg.applyEnv();
    return cfg;
  }

  get(): Readonly<McpConfigState> {
    return structuredClone(this.state);
  }

  update(patch: Partial<McpConfigState>): Readonly<McpConfigState> {
    this.state = mergeConfig(this.state, patch);
    return this.get();
  }

  applyEnv(): void {
    if (process.env["ADOS_MCP_ENABLED"] !== undefined) {
      this.state.enabled = process.env["ADOS_MCP_ENABLED"] === "1" || process.env["ADOS_MCP_ENABLED"] === "true";
    }
    if (process.env["ADOS_MCP_HOST"]) this.state.host = process.env["ADOS_MCP_HOST"];
    if (process.env["ADOS_MCP_PORT"]) {
      this.state.port = Number(process.env["ADOS_MCP_PORT"]);
    }
    if (process.env["ADOS_MCP_TOKEN"]) {
      this.state.authentication.defaultAdminToken = process.env["ADOS_MCP_TOKEN"];
    }
    if (process.env["ADOS_RUNTIME_URL"]) {
      this.state.runtime.baseUrl = process.env["ADOS_RUNTIME_URL"].replace(/\/$/, "");
    }
  }
}

function mergeConfig(
  base: McpConfigState,
  patch: Partial<McpConfigState>,
): McpConfigState {
  return {
    enabled: patch.enabled ?? base.enabled,
    host: patch.host ?? base.host,
    port: patch.port ?? base.port,
    transport: patch.transport ?? base.transport,
    authentication: {
      ...base.authentication,
      ...(patch.authentication ?? {}),
    },
    permissions: {
      ...base.permissions,
      ...(patch.permissions ?? {}),
    },
    runtime: {
      ...base.runtime,
      ...(patch.runtime ?? {}),
    },
    logging: {
      ...base.logging,
      ...(patch.logging ?? {}),
    },
  };
}

export function createMCPConfig(initial?: Partial<McpConfigState>): MCPConfig {
  return new MCPConfig(initial);
}
