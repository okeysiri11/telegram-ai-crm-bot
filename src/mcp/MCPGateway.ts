import {
  MCPConfig,
  createMCPConfig,
  type McpConfigState,
} from "./MCPConfig.js";
import { MCPEvents, createMCPEvents } from "./MCPEvents.js";
import { MCPPermissions, createMCPPermissions } from "./MCPPermissions.js";
import {
  MCPAuthentication,
  createMCPAuthentication,
} from "./MCPAuthentication.js";
import {
  MCPSessionManager,
  createMCPSessionManager,
} from "./MCPSession.js";
import { MCPRegistry, createMCPRegistry } from "./MCPRegistry.js";
import { MCPTransport, createMCPTransport } from "./MCPTransport.js";
import { MCPServer, createMCPServer } from "./MCPServer.js";
import type {
  McpJsonRpcRequest,
  McpPermissionLevel,
  RuntimeInvoker,
} from "./types.js";
import type { McpEventListener } from "./MCPEvents.js";

export interface MCPGatewayOptions {
  readonly config?: Partial<McpConfigState>;
  readonly loadDiskConfig?: boolean;
}

/**
 * Enterprise MCP Gateway facade — Claude Desktop / MCP clients → Runtime API.
 */
export class MCPGateway {
  readonly config: MCPConfig;
  readonly events: MCPEvents;
  readonly permissions: MCPPermissions;
  readonly auth: MCPAuthentication;
  readonly sessions: MCPSessionManager;
  readonly registry: MCPRegistry;
  readonly transport: MCPTransport;
  readonly server: MCPServer;

  private enabled: boolean;

  constructor(options: MCPGatewayOptions = {}) {
    this.config = options.loadDiskConfig
      ? MCPConfig.loadFromDisk()
      : createMCPConfig(options.config);
    if (options.config) this.config.update(options.config);
    const cfg = this.config.get();
    this.enabled = cfg.enabled;
    this.events = createMCPEvents();
    this.permissions = createMCPPermissions();
    this.auth = createMCPAuthentication(this.config);
    this.sessions = createMCPSessionManager();
    this.registry = createMCPRegistry();
    this.transport = createMCPTransport({
      kind: cfg.transport,
      httpBaseUrl: cfg.runtime.baseUrl,
    });
    this.server = createMCPServer({
      registry: this.registry,
      transport: this.transport,
      auth: this.auth,
      permissions: this.permissions,
      events: this.events,
      sessions: this.sessions,
      config: this.config,
    });
  }

  on(listener: McpEventListener): () => void {
    return this.events.on(listener);
  }

  /**
   * Bind in-process Runtime dispatch (preferred). Avoids duplicating Runtime logic.
   */
  setRuntimeInvoker(invoker: RuntimeInvoker | null): void {
    this.transport.setRuntimeInvoker(invoker);
  }

  connectClient(input: {
    clientId: string;
    token?: string | null;
    transport?: string;
  }) {
    const auth = this.auth.authenticate(input.token);
    if (!auth.ok) {
      this.events.emit("mcp.permission.denied", {
        clientId: input.clientId,
        reason: auth.reason,
      });
      throw new Error(auth.reason ?? "Unauthorized");
    }
    const session = this.sessions.connect({
      clientId: input.clientId,
      permission: auth.permission,
      transport: input.transport ?? this.config.get().transport,
    });
    this.events.emit("mcp.connected", session.snapshot());
    if (this.config.get().logging.connections) {
      this.events.log("connection", `connected ${input.clientId}`, {
        sessionId: session.id,
      });
    }
    return session.snapshot();
  }

  disconnectClient(sessionId: string) {
    const session = this.sessions.disconnect(sessionId);
    if (session) {
      this.events.emit("mcp.disconnected", session.snapshot());
      if (this.config.get().logging.connections) {
        this.events.log("connection", `disconnected ${session.clientId}`, {
          sessionId,
        });
      }
    }
    return session?.snapshot() ?? null;
  }

  async handleRpc(
    request: McpJsonRpcRequest,
    ctx?: {
      token?: string | null;
      clientId?: string;
      sessionId?: string;
    },
  ) {
    return this.server.handle(request, ctx ?? {});
  }

  /** Convenience: call a registered tool through MCP (still via Runtime). */
  async callTool(
    name: string,
    args: Record<string, unknown> = {},
    token?: string | null,
  ) {
    const ctx: {
      token?: string | null;
      clientId?: string;
      sessionId?: string;
    } = {};
    if (token !== undefined) ctx.token = token;
    return this.handleRpc(
      {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: { name, arguments: args },
      },
      ctx,
    );
  }

  issueToken(permission: McpPermissionLevel = "admin") {
    return this.auth.issueToken(permission);
  }

  status() {
    const cfg = this.config.get();
    const metrics = this.server.metrics();
    const snap = this.registry.snapshot();
    return {
      id: "ados.mcp",
      name: "Enterprise MCP Gateway",
      health: this.enabled ? ("OK" as const) : ("DOWN" as const),
      enabled: this.enabled,
      transport: cfg.transport,
      host: cfg.host,
      port: cfg.port,
      runtimeBound: this.transport.hasInvoker(),
      runtimeBaseUrl: cfg.runtime.baseUrl,
      connectedClients: this.sessions.activeCount(),
      sessions: this.sessions.list(),
      tools: snap.tools.length,
      resources: snap.resources.length,
      prompts: snap.prompts.length,
      permissions: ["read", "execute", "admin"] as const,
      requests: metrics.requests,
      errors: metrics.errors,
      authSessions: this.auth.listSessions(),
      recentLogs: this.events.listLogs(20),
    };
  }

  listTools() {
    return this.registry.tools.list();
  }

  listResources() {
    return this.registry.resources.list();
  }

  listPrompts() {
    return this.registry.prompts.list();
  }

  getConfig(): McpConfigState {
    return this.config.get();
  }
}

export function createMCPGateway(options?: MCPGatewayOptions): MCPGateway {
  return new MCPGateway(options);
}
