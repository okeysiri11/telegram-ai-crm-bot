import type { McpResourceDefinition } from "./types.js";

export function createBuiltinResources(): McpResourceDefinition[] {
  return [
    {
      uri: "ados://architecture",
      name: "Architecture",
      description: "Kernel and platform architecture snapshot",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/kernel",
    },
    {
      uri: "ados://sprint",
      name: "Current Sprint",
      description: "Current platform status as sprint pulse",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/status",
    },
    {
      uri: "ados://documentation",
      name: "Documentation",
      description: "Runtime root endpoint catalog",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/",
    },
    {
      uri: "ados://knowledge",
      name: "Knowledge Base",
      description: "Recent platform events (knowledge stream)",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/events",
    },
    {
      uri: "ados://modules",
      name: "Module List",
      description: "Registered services / modules",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/services",
    },
    {
      uri: "ados://providers",
      name: "Registered Providers",
      description: "Provider Gateway registry",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/providers",
    },
    {
      uri: "ados://agents",
      name: "Registered Agents",
      description: "AI Orchestrator agents",
      mimeType: "application/json",
      permission: "read",
      runtimePath: "/agents",
    },
    {
      uri: "ados://configuration",
      name: "Current Configuration",
      description: "Kernel configuration surface",
      mimeType: "application/json",
      permission: "admin",
      runtimePath: "/kernel",
    },
  ];
}

export class MCPResources {
  private readonly resources = new Map<string, McpResourceDefinition>();

  constructor(initial?: readonly McpResourceDefinition[]) {
    for (const r of initial ?? createBuiltinResources()) {
      this.register(r);
    }
  }

  register(resource: McpResourceDefinition): void {
    this.resources.set(resource.uri, resource);
  }

  get(uri: string): McpResourceDefinition | undefined {
    return this.resources.get(uri);
  }

  list(): McpResourceDefinition[] {
    return [...this.resources.values()];
  }
}

export function createMCPResources(
  initial?: readonly McpResourceDefinition[],
): MCPResources {
  return new MCPResources(initial);
}
