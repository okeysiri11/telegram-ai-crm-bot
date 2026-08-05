/**
 * ADOS MCP Gateway — shared types.
 */

export type McpPermissionLevel = "read" | "execute" | "admin";

export type McpTransportKind = "stdio" | "http" | "http+stdio";

export interface RuntimeRequestResult {
  readonly status: number;
  readonly body: unknown;
}

/**
 * Port into Runtime API — MCP never reaches Orchestrator/Providers directly.
 */
export type RuntimeInvoker = (
  method: string,
  path: string,
  body?: unknown,
  search?: URLSearchParams,
) => Promise<RuntimeRequestResult>;

export interface McpToolDefinition {
  readonly name: string;
  readonly description: string;
  readonly permission: McpPermissionLevel;
  readonly inputSchema: Readonly<Record<string, unknown>>;
  readonly runtime: {
    readonly method: "GET" | "POST";
    readonly path: string;
    readonly mapArgs?: (args: Readonly<Record<string, unknown>>) => unknown;
  };
}

export interface McpResourceDefinition {
  readonly uri: string;
  readonly name: string;
  readonly description: string;
  readonly mimeType: string;
  readonly permission: McpPermissionLevel;
  readonly runtimePath: string;
  readonly runtimeMethod?: "GET" | "POST";
}

export interface McpPromptDefinition {
  readonly name: string;
  readonly description: string;
  readonly permission: McpPermissionLevel;
  readonly arguments: readonly {
    readonly name: string;
    readonly description: string;
    readonly required: boolean;
  }[];
  readonly template: string;
}

export type McpEventType =
  | "mcp.connected"
  | "mcp.disconnected"
  | "mcp.tool.called"
  | "mcp.tool.completed"
  | "mcp.resource.read"
  | "mcp.permission.denied";

export interface McpEvent {
  readonly type: McpEventType;
  readonly at: string;
  readonly payload: unknown;
}

export interface McpLogEntry {
  readonly id: string;
  readonly at: string;
  readonly kind:
    | "connection"
    | "tool"
    | "resource"
    | "permission"
    | "error"
    | "latency";
  readonly message: string;
  readonly meta?: Readonly<Record<string, unknown>>;
}

export interface McpJsonRpcRequest {
  readonly jsonrpc: "2.0";
  readonly id?: string | number | null;
  readonly method: string;
  readonly params?: unknown;
}

export interface McpJsonRpcResponse {
  readonly jsonrpc: "2.0";
  readonly id: string | number | null;
  readonly result?: unknown;
  readonly error?: { code: number; message: string; data?: unknown };
}
