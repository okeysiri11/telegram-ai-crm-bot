import type { IProvider } from "./interfaces/IProvider.js";
import type {
  ProviderCapability,
  ProviderConfiguration,
  ProviderConnectionStatus,
  ProviderExecuteRequest,
  ProviderExecuteResult,
  ProviderHealth,
  ProviderMetrics,
  ProviderSnapshot,
} from "./types.js";

export interface BaseProviderOptions {
  readonly id: string;
  readonly name: string;
  readonly kind: string;
  readonly capabilities: readonly ProviderCapability[];
  readonly models?: readonly string[];
  readonly baseUrl?: string;
  readonly latencyMs?: { min: number; max: number };
  readonly notes?: string;
}

/**
 * Mock-capable provider base — simulates latency, tracks metrics, no API keys.
 */
export abstract class BaseProvider implements IProvider {
  readonly id: string;
  readonly name: string;

  private readonly caps: readonly ProviderCapability[];
  private readonly config: ProviderConfiguration;
  private readonly latency: { min: number; max: number };
  private status: ProviderConnectionStatus = "disconnected";
  private currentRequests = 0;
  private totalRequests = 0;
  private successes = 0;
  private errors = 0;
  private totalDurationMs = 0;
  private lastLatencyMs = 0;

  constructor(options: BaseProviderOptions) {
    this.id = options.id;
    this.name = options.name;
    this.caps = options.capabilities;
    this.latency = options.latencyMs ?? { min: 30, max: 90 };
    this.config = {
      id: options.id,
      name: options.name,
      kind: options.kind,
      mock: true,
      ...(options.baseUrl !== undefined ? { baseUrl: options.baseUrl } : {}),
      ...(options.models !== undefined ? { models: options.models } : {}),
      ...(options.notes !== undefined
        ? { notes: options.notes }
        : { notes: "Mock adapter — no real API keys required" }),
    };
  }

  capabilities(): readonly ProviderCapability[] {
    return this.caps;
  }

  configuration(): ProviderConfiguration {
    return this.config;
  }

  async connect(): Promise<void> {
    if (this.status === "connected") return;
    this.status = "connecting";
    await sleep(rand(15, 40));
    this.status = "connected";
  }

  async disconnect(): Promise<void> {
    if (this.status === "disconnected") return;
    await sleep(10);
    this.status = "disconnected";
  }

  async cancel(_requestId?: string): Promise<void> {
    // Mock: clear in-flight bookkeeping
    this.currentRequests = 0;
    if (this.status === "connected") {
      this.status = "connected";
    }
  }

  health(): ProviderHealth {
    const checkedAt = new Date().toISOString();
    if (this.status === "error") {
      return {
        status: "DOWN",
        message: "Provider in error state",
        checkedAt,
        latencyMs: this.lastLatencyMs,
      };
    }
    if (this.status !== "connected") {
      return {
        status: "DOWN",
        message: "Not connected",
        checkedAt,
      };
    }
    return {
      status: "OK",
      checkedAt,
      ...(this.lastLatencyMs > 0 ? { latencyMs: this.lastLatencyMs } : {}),
    };
  }

  metrics(): ProviderMetrics {
    return {
      totalRequests: this.totalRequests,
      successes: this.successes,
      errors: this.errors,
      avgResponseTimeMs:
        this.totalRequests === 0
          ? 0
          : Math.round(this.totalDurationMs / this.totalRequests),
      currentRequests: this.currentRequests,
      load: this.currentRequests,
    };
  }

  snapshot(): ProviderSnapshot {
    const m = this.metrics();
    return {
      id: this.id,
      name: this.name,
      status: this.status,
      connected: this.status === "connected",
      health: this.health(),
      capabilities: this.caps,
      currentRequests: m.currentRequests,
      averageResponseTimeMs: m.avgResponseTimeMs,
      totalRequests: m.totalRequests,
      errors: m.errors,
      metrics: m,
      configuration: this.config,
    };
  }

  async execute(request: ProviderExecuteRequest): Promise<ProviderExecuteResult> {
    if (this.status !== "connected") {
      return this.fail(request, "Provider not connected", 0);
    }
    const supported = this.caps.some(
      (c) => c.id === request.capability || request.capability.startsWith(c.id),
    );
    if (!supported && !this.caps.some((c) => c.id === "*")) {
      // allow generic completion-like capabilities
      const genericOk = ["completion", "chat", "generate", "code", "search"].some(
        (p) => request.capability.toLowerCase().includes(p),
      );
      if (!genericOk) {
        return this.fail(
          request,
          `Capability not supported: ${request.capability}`,
          0,
        );
      }
    }

    this.currentRequests += 1;
    const started = Date.now();
    try {
      await sleep(rand(this.latency.min, this.latency.max));
      const output = await this.mockExecute(request);
      const durationMs = Date.now() - started;
      this.recordSuccess(durationMs);
      return {
        requestId: request.requestId,
        providerId: this.id,
        ok: true,
        output,
        durationMs,
        completedAt: new Date().toISOString(),
      };
    } catch (error) {
      const durationMs = Date.now() - started;
      const message = error instanceof Error ? error.message : String(error);
      this.recordError(durationMs);
      return this.fail(request, message, durationMs);
    } finally {
      this.currentRequests = Math.max(0, this.currentRequests - 1);
    }
  }

  /** Mock response body — subclasses customize flavor. */
  protected abstract mockExecute(
    request: ProviderExecuteRequest,
  ): Promise<unknown> | unknown;

  private fail(
    request: ProviderExecuteRequest,
    message: string,
    durationMs: number,
  ): ProviderExecuteResult {
    return {
      requestId: request.requestId,
      providerId: this.id,
      ok: false,
      output: null,
      error: message,
      durationMs,
      completedAt: new Date().toISOString(),
    };
  }

  private recordSuccess(durationMs: number): void {
    this.totalRequests += 1;
    this.successes += 1;
    this.totalDurationMs += durationMs;
    this.lastLatencyMs = durationMs;
  }

  private recordError(durationMs: number): void {
    this.totalRequests += 1;
    this.errors += 1;
    this.totalDurationMs += durationMs;
    this.lastLatencyMs = durationMs;
    this.status = "error";
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function rand(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1));
}
