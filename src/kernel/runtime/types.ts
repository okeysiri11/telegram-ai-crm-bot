/**
 * Runtime Server types.
 * Depends only on Kernel / Event Bus / Service Registry / Workflow Engine.
 */

export interface RuntimeServerOptions {
  readonly host?: string;
  readonly port?: number;
  readonly platformVersion?: string;
}

export interface HealthResponse {
  readonly status: "ok";
}

export interface StatusResponse {
  readonly version: string;
  readonly kernel: "OK";
  readonly eventBus: "OK";
  readonly serviceMesh: "OK";
  readonly workflowEngine: "OK";
  readonly runtimeServer: "OK";
  readonly orchestrator: "OK" | "DOWN";
  readonly providerGateway: "OK" | "DOWN";
  readonly chatBridge: "OK" | "DOWN";
  readonly voice: "OK" | "DOWN";
  readonly mcp: "OK" | "DOWN";
  readonly execution: "OK" | "DOWN";
  readonly services: number;
  readonly agents: number;
  readonly providers: number;
  readonly providersConnected: number;
  readonly runningTasks: number;
  readonly queueSize: number;
  readonly systemStatus: "READY" | "DEGRADED" | "DOWN";
}

export interface AgentListItem {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly status: string;
  readonly provider: string;
  readonly memory: string;
  readonly skills?: readonly string[];
  readonly version?: string;
  readonly lastExecution?: string | null;
  readonly currentTask: string | null;
  readonly queueSize: number;
  readonly runningTasks: number;
  readonly responseTimeMs: number;
  readonly health: string;
  readonly metrics: {
    readonly tasksCompleted: number;
    readonly successes: number;
    readonly errors: number;
    readonly avgResponseTimeMs: number;
    readonly load: number;
  };
}

export interface ServiceListItem {
  readonly id: string;
  readonly version: string;
  readonly kind: string;
  readonly lifecycle: string;
  readonly uptimeMs: number;
  readonly health: string;
  readonly dependencies: readonly string[];
}

export interface WorkflowListItem {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly start: string;
  readonly steps: number;
}

export interface MetricsResponse {
  readonly uptimeSec: number;
  readonly memory: {
    readonly rss: number;
    readonly heapUsed: number;
    readonly heapTotal: number;
    readonly external: number;
  };
  readonly cpu: {
    readonly userMicros: number;
    readonly systemMicros: number;
  };
  readonly startedAt: string;
}

export interface LogEntry {
  readonly id: string;
  readonly at: string;
  readonly level: "info" | "warn" | "error";
  readonly message: string;
  readonly source?: string;
}

export interface EventEntry {
  readonly id: string;
  readonly type: string;
  readonly at: string;
  readonly payload?: unknown;
}

export interface KernelInfoResponse {
  readonly version: string;
  readonly platformVersion: string;
  readonly state: string;
  readonly startedAt: string;
  readonly uptimeMs: number;
  readonly modules: readonly string[];
  readonly services: number;
  readonly health: string;
}
