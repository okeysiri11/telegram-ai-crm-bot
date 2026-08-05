import type { McpToolDefinition } from "./types.js";

/**
 * Built-in MCP tools — each maps to a Runtime API path (no internal bypass).
 */
export function createBuiltinTools(): McpToolDefinition[] {
  return [
    tool("system.status", "ADOS system status", "read", "GET", "/status"),
    tool("system.health", "Health probe", "read", "GET", "/health"),
    tool("system.version", "Platform version from status", "read", "GET", "/status"),
    tool("runtime.status", "Runtime status", "read", "GET", "/status"),
    tool("runtime.metrics", "Runtime metrics", "read", "GET", "/metrics"),
    tool("agent.list", "List AI agents", "read", "GET", "/agents"),
    tool("agent.info", "Agent status overview", "read", "GET", "/agents/status"),
    {
      name: "agent.execute",
      description: "Execute an agent via Orchestrator (Runtime)",
      permission: "execute",
      inputSchema: {
        type: "object",
        properties: {
          agentId: { type: "string" },
          task: { type: "string" },
          type: { type: "string" },
          payload: { type: "object" },
        },
        required: ["agentId"],
      },
      runtime: {
        method: "POST",
        path: "/agents/run",
        mapArgs: (args) => ({
          agentId: args["agentId"],
          ...(args["task"] !== undefined ? { task: args["task"] } : {}),
          ...(args["type"] !== undefined ? { type: args["type"] } : {}),
          ...(args["payload"] !== undefined ? { payload: args["payload"] } : {}),
        }),
      },
    },
    tool("workflow.list", "List workflows", "read", "GET", "/workflow"),
    {
      name: "workflow.execute",
      description: "Start a collaboration / workflow via Runtime",
      permission: "execute",
      inputSchema: {
        type: "object",
        properties: {
          templateId: { type: "string" },
          name: { type: "string" },
          goal: { type: "string" },
        },
      },
      runtime: {
        method: "POST",
        path: "/workflow/start",
        mapArgs: (args) => args,
      },
    },
    tool("provider.list", "List providers", "read", "GET", "/providers"),
    tool("provider.status", "Provider gateway status", "read", "GET", "/providers/status"),
    tool("project.list", "List services / modules as projects", "read", "GET", "/services"),
    tool("project.info", "Kernel project info", "read", "GET", "/kernel"),
    tool("knowledge.search", "Search knowledge / events", "read", "GET", "/events"),
    tool("document.search", "Search logs as documents", "read", "GET", "/logs"),
    tool("dashboard.status", "Dashboard / system status", "read", "GET", "/status"),
    tool("voice.status", "Enterprise Voice status", "read", "GET", "/voice/status"),
  ];
}

function tool(
  name: string,
  description: string,
  permission: McpToolDefinition["permission"],
  method: "GET" | "POST",
  path: string,
): McpToolDefinition {
  return {
    name,
    description,
    permission,
    inputSchema: { type: "object", properties: {} },
    runtime: { method, path },
  };
}

export class MCPToolRegistry {
  private readonly tools = new Map<string, McpToolDefinition>();

  constructor(initial?: readonly McpToolDefinition[]) {
    for (const t of initial ?? createBuiltinTools()) {
      this.register(t);
    }
  }

  register(toolDef: McpToolDefinition): void {
    this.tools.set(toolDef.name, toolDef);
  }

  get(name: string): McpToolDefinition | undefined {
    return this.tools.get(name);
  }

  list(): McpToolDefinition[] {
    return [...this.tools.values()];
  }

  names(): string[] {
    return [...this.tools.keys()];
  }
}

export function createMCPToolRegistry(
  initial?: readonly McpToolDefinition[],
): MCPToolRegistry {
  return new MCPToolRegistry(initial);
}
