import type { McpTransportKind, RuntimeInvoker, RuntimeRequestResult } from "./types.js";

/**
 * Transport abstraction for MCP (stdio / http).
 * Runtime traffic always goes through RuntimeInvoker — never direct module imports.
 */
export class MCPTransport {
  readonly kind: McpTransportKind;
  private invoker: RuntimeInvoker | null = null;
  private readonly httpBaseUrl: string;

  constructor(options: {
    kind: McpTransportKind;
    httpBaseUrl?: string;
  }) {
    this.kind = options.kind;
    this.httpBaseUrl = (options.httpBaseUrl ?? "http://127.0.0.1:3000").replace(
      /\/$/,
      "",
    );
  }

  setRuntimeInvoker(invoker: RuntimeInvoker | null): void {
    this.invoker = invoker;
  }

  hasInvoker(): boolean {
    return this.invoker !== null;
  }

  async invokeRuntime(
    method: string,
    path: string,
    body?: unknown,
    search?: URLSearchParams,
  ): Promise<RuntimeRequestResult> {
    if (this.invoker) {
      return this.invoker(method, path, body, search);
    }
    // Fallback HTTP to Runtime (Claude Desktop / external process scenarios)
    const url = new URL(path, this.httpBaseUrl);
    if (search) {
      for (const [k, v] of search.entries()) url.searchParams.set(k, v);
    }
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      ...(body !== undefined && method !== "GET"
        ? { body: JSON.stringify(body) }
        : {}),
    });
    const json = (await response.json()) as unknown;
    return { status: response.status, body: json };
  }
}

export function createMCPTransport(options: {
  kind: McpTransportKind;
  httpBaseUrl?: string;
}): MCPTransport {
  return new MCPTransport(options);
}
