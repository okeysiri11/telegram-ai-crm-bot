import type {
  McpJsonRpcRequest,
  McpJsonRpcResponse,
  McpPermissionLevel,
} from "./types.js";
import type { MCPRegistry } from "./MCPRegistry.js";
import type { MCPTransport } from "./MCPTransport.js";
import type { MCPAuthentication } from "./MCPAuthentication.js";
import type { MCPPermissions } from "./MCPPermissions.js";
import type { MCPEvents } from "./MCPEvents.js";
import type { MCPSessionManager } from "./MCPSession.js";
import { McpPermissionError } from "./MCPPermissions.js";
import type { MCPConfig } from "./MCPConfig.js";

export interface McpCallContext {
  readonly token?: string | null;
  readonly clientId?: string;
  readonly sessionId?: string;
  readonly transport?: string;
}

/**
 * MCP JSON-RPC server surface (tools/list, tools/call, resources/*, prompts/*).
 */
export class MCPServer {
  private requestCount = 0;
  private errorCount = 0;

  constructor(
    private readonly registry: MCPRegistry,
    private readonly transport: MCPTransport,
    private readonly auth: MCPAuthentication,
    _permissions: MCPPermissions,
    private readonly events: MCPEvents,
    private readonly sessions: MCPSessionManager,
    private readonly config: MCPConfig,
  ) {
    void _permissions;
  }

  metrics() {
    return {
      requests: this.requestCount,
      errors: this.errorCount,
    };
  }

  async handle(
    request: McpJsonRpcRequest,
    ctx: McpCallContext = {},
  ): Promise<McpJsonRpcResponse> {
    const id = request.id ?? null;
    this.requestCount += 1;
    const started = Date.now();
    try {
      const result = await this.dispatch(request.method, request.params, ctx);
      const latencyMs = Date.now() - started;
      if (this.config.get().logging.latency) {
        this.events.log("latency", `${request.method} ${latencyMs}ms`, {
          method: request.method,
          latencyMs,
        });
      }
      if (ctx.sessionId) this.sessions.get(ctx.sessionId)?.touch(true);
      return { jsonrpc: "2.0", id, result };
    } catch (error) {
      this.errorCount += 1;
      if (ctx.sessionId) this.sessions.get(ctx.sessionId)?.touch(false);
      const message = error instanceof Error ? error.message : String(error);
      const code =
        error instanceof McpPermissionError ? -32001 : -32000;
      if (error instanceof McpPermissionError) {
        this.events.emit("mcp.permission.denied", {
          method: request.method,
          message,
        });
        if (this.config.get().logging.permissionFailures) {
          this.events.log("permission", message, { method: request.method });
        }
      } else {
        this.events.log("error", message, { method: request.method });
      }
      return {
        jsonrpc: "2.0",
        id,
        error: { code, message },
      };
    }
  }

  private async dispatch(
    method: string,
    params: unknown,
    ctx: McpCallContext,
  ): Promise<unknown> {
    switch (method) {
      case "initialize":
        return {
          protocolVersion: "2024-11-05",
          serverInfo: {
            name: "ados-mcp-gateway",
            version: "4.2.0",
          },
          capabilities: {
            tools: {},
            resources: {},
            prompts: {},
          },
        };
      case "ping":
        return {};
      case "tools/list":
        this.requirePermission(ctx, "read");
        return {
          tools: this.registry.tools.list().map((t) => ({
            name: t.name,
            description: t.description,
            inputSchema: t.inputSchema,
            annotations: { permission: t.permission },
          })),
        };
      case "tools/call":
        return this.callTool(params, ctx);
      case "resources/list":
        this.requirePermission(ctx, "read");
        return {
          resources: this.registry.resources.list().map((r) => ({
            uri: r.uri,
            name: r.name,
            description: r.description,
            mimeType: r.mimeType,
          })),
        };
      case "resources/read":
        return this.readResource(params, ctx);
      case "prompts/list":
        this.requirePermission(ctx, "read");
        return {
          prompts: this.registry.prompts.list().map((p) => ({
            name: p.name,
            description: p.description,
            arguments: p.arguments,
          })),
        };
      case "prompts/get":
        return this.getPrompt(params, ctx);
      default:
        throw new Error(`Method not found: ${method}`);
    }
  }

  private requirePermission(
    ctx: McpCallContext,
    required: McpPermissionLevel,
  ): McpPermissionLevel {
    const auth = this.auth.validateRuntimeAccess({
      required,
      ...(ctx.token !== undefined ? { token: ctx.token as string | null } : {}),
    });
    if (!auth.ok) {
      throw new McpPermissionError(auth.reason ?? "Unauthorized");
    }
    return auth.permission;
  }

  private async callTool(
    params: unknown,
    ctx: McpCallContext,
  ): Promise<unknown> {
    const p = (params ?? {}) as {
      name?: string;
      arguments?: Record<string, unknown>;
    };
    if (!p.name) throw new Error("tools/call requires name");
    const tool = this.registry.tools.get(p.name);
    if (!tool) throw new Error(`Unknown tool: ${p.name}`);

    this.requirePermission(ctx, tool.permission);
    this.events.emit("mcp.tool.called", { name: tool.name, args: p.arguments });
    if (this.config.get().logging.toolCalls) {
      this.events.log("tool", `call ${tool.name}`, { args: p.arguments });
    }

    const started = Date.now();
    const body =
      tool.runtime.mapArgs && p.arguments
        ? tool.runtime.mapArgs(p.arguments)
        : p.arguments;
    const result = await this.transport.invokeRuntime(
      tool.runtime.method,
      tool.runtime.path,
      body,
    );
    const latencyMs = Date.now() - started;
    this.events.emit("mcp.tool.completed", {
      name: tool.name,
      status: result.status,
      latencyMs,
    });
    if (this.config.get().logging.toolCalls) {
      this.events.log("tool", `completed ${tool.name}`, {
        status: result.status,
        latencyMs,
      });
    }
    if (result.status >= 400) {
      throw new Error(
        typeof result.body === "object" &&
          result.body &&
          "error" in (result.body as object)
          ? String((result.body as { error: unknown }).error)
          : `Runtime error ${result.status}`,
      );
    }
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result.body, null, 2),
        },
      ],
      isError: false,
      structuredContent: result.body,
    };
  }

  private async readResource(
    params: unknown,
    ctx: McpCallContext,
  ): Promise<unknown> {
    const p = (params ?? {}) as { uri?: string };
    if (!p.uri) throw new Error("resources/read requires uri");
    const resource = this.registry.resources.get(p.uri);
    if (!resource) throw new Error(`Unknown resource: ${p.uri}`);
    this.requirePermission(ctx, resource.permission);
    this.events.emit("mcp.resource.read", { uri: resource.uri });
    if (this.config.get().logging.resourceReads) {
      this.events.log("resource", `read ${resource.uri}`);
    }
    const result = await this.transport.invokeRuntime(
      resource.runtimeMethod ?? "GET",
      resource.runtimePath,
    );
    if (result.status >= 400) {
      throw new Error(`Runtime error ${result.status}`);
    }
    return {
      contents: [
        {
          uri: resource.uri,
          mimeType: resource.mimeType,
          text: JSON.stringify(result.body, null, 2),
        },
      ],
    };
  }

  private getPrompt(params: unknown, ctx: McpCallContext): unknown {
    const p = (params ?? {}) as {
      name?: string;
      arguments?: Record<string, string>;
    };
    if (!p.name) throw new Error("prompts/get requires name");
    const prompt = this.registry.prompts.get(p.name);
    if (!prompt) throw new Error(`Unknown prompt: ${p.name}`);
    this.requirePermission(ctx, prompt.permission);
    return this.registry.prompts.render(p.name, p.arguments ?? {});
  }
}

export function createMCPServer(deps: {
  registry: MCPRegistry;
  transport: MCPTransport;
  auth: MCPAuthentication;
  permissions: MCPPermissions;
  events: MCPEvents;
  sessions: MCPSessionManager;
  config: MCPConfig;
}): MCPServer {
  return new MCPServer(
    deps.registry,
    deps.transport,
    deps.auth,
    deps.permissions,
    deps.events,
    deps.sessions,
    deps.config,
  );
}
