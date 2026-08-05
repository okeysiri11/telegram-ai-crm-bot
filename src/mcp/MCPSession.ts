export interface McpSessionSnapshot {
  readonly id: string;
  readonly clientId: string;
  readonly connectedAt: string;
  readonly lastSeenAt: string;
  readonly permission: string;
  readonly transport: string;
  readonly requestCount: number;
  readonly errorCount: number;
  readonly active: boolean;
}

/**
 * MCP client session tracking.
 */
export class MCPSession {
  readonly id: string;
  readonly clientId: string;
  readonly connectedAt: string;
  readonly permission: string;
  readonly transport: string;
  private lastSeenAt: string;
  private requestCount = 0;
  private errorCount = 0;
  private active = true;

  constructor(input: {
    clientId: string;
    permission: string;
    transport: string;
    id?: string;
  }) {
    this.id =
      input.id ??
      `mcps_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    this.clientId = input.clientId;
    this.permission = input.permission;
    this.transport = input.transport;
    this.connectedAt = new Date().toISOString();
    this.lastSeenAt = this.connectedAt;
  }

  touch(ok = true): void {
    this.lastSeenAt = new Date().toISOString();
    this.requestCount += 1;
    if (!ok) this.errorCount += 1;
  }

  disconnect(): void {
    this.active = false;
    this.lastSeenAt = new Date().toISOString();
  }

  snapshot(): McpSessionSnapshot {
    return {
      id: this.id,
      clientId: this.clientId,
      connectedAt: this.connectedAt,
      lastSeenAt: this.lastSeenAt,
      permission: this.permission,
      transport: this.transport,
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      active: this.active,
    };
  }
}

export class MCPSessionManager {
  private readonly sessions = new Map<string, MCPSession>();

  connect(input: {
    clientId: string;
    permission: string;
    transport: string;
  }): MCPSession {
    const session = new MCPSession(input);
    this.sessions.set(session.id, session);
    return session;
  }

  get(id: string): MCPSession | undefined {
    return this.sessions.get(id);
  }

  disconnect(id: string): MCPSession | undefined {
    const s = this.sessions.get(id);
    s?.disconnect();
    return s;
  }

  list(activeOnly = false): McpSessionSnapshot[] {
    return [...this.sessions.values()]
      .map((s) => s.snapshot())
      .filter((s) => (activeOnly ? s.active : true));
  }

  activeCount(): number {
    return this.list(true).length;
  }
}

export function createMCPSessionManager(): MCPSessionManager {
  return new MCPSessionManager();
}
