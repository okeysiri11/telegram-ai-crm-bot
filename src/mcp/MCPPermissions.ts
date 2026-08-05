import type { McpPermissionLevel } from "./types.js";

const RANK: Record<McpPermissionLevel, number> = {
  read: 1,
  execute: 2,
  admin: 3,
};

/**
 * Permission levels: Read < Execute < Admin.
 */
export class MCPPermissions {
  allows(granted: McpPermissionLevel, required: McpPermissionLevel): boolean {
    return RANK[granted] >= RANK[required];
  }

  assert(granted: McpPermissionLevel, required: McpPermissionLevel): void {
    if (!this.allows(granted, required)) {
      throw new McpPermissionError(
        `Permission denied: requires ${required}, granted ${granted}`,
      );
    }
  }

  parse(level: string | undefined, fallback: McpPermissionLevel): McpPermissionLevel {
    if (level === "read" || level === "execute" || level === "admin") return level;
    return fallback;
  }
}

export class McpPermissionError extends Error {
  readonly code = "mcp.permission.denied";
  constructor(message: string) {
    super(message);
    this.name = "McpPermissionError";
  }
}

export function createMCPPermissions(): MCPPermissions {
  return new MCPPermissions();
}
