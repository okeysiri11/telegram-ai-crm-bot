import { MCPToolRegistry, createMCPToolRegistry } from "./MCPToolRegistry.js";
import { MCPResources, createMCPResources } from "./MCPResources.js";
import { MCPPrompts, createMCPPrompts } from "./MCPPrompts.js";

/**
 * Aggregate registry of tools, resources, and prompts.
 */
export class MCPRegistry {
  readonly tools: MCPToolRegistry;
  readonly resources: MCPResources;
  readonly prompts: MCPPrompts;

  constructor(options?: {
    tools?: MCPToolRegistry;
    resources?: MCPResources;
    prompts?: MCPPrompts;
  }) {
    this.tools = options?.tools ?? createMCPToolRegistry();
    this.resources = options?.resources ?? createMCPResources();
    this.prompts = options?.prompts ?? createMCPPrompts();
  }

  snapshot() {
    return {
      tools: this.tools.list().map((t) => ({
        name: t.name,
        description: t.description,
        permission: t.permission,
      })),
      resources: this.resources.list().map((r) => ({
        uri: r.uri,
        name: r.name,
        description: r.description,
        permission: r.permission,
      })),
      prompts: this.prompts.list().map((p) => ({
        name: p.name,
        description: p.description,
        permission: p.permission,
      })),
    };
  }
}

export function createMCPRegistry(): MCPRegistry {
  return new MCPRegistry();
}
