import { createBuiltinProviders } from "./adapters/builtin.js";
import { ProviderRegistry } from "./ProviderRegistry.js";
import type { IProvider } from "./interfaces/IProvider.js";
import type {
  GatewayStatus,
  ProviderEventType,
  ProviderExecuteResult,
  ProviderSnapshot,
} from "./types.js";

export type ProviderGatewayListener = (event: {
  type: ProviderEventType;
  payload: unknown;
}) => void;

export interface SelectProviderOptions {
  readonly preferredId?: string;
  /** Maps agent provider aliases: cursor|openai|claude|github|local */
  readonly preferredAlias?: string;
  readonly capability?: string;
}

/**
 * Single entry for all external AI providers.
 * Orchestrator selects providers here — never calls adapters directly.
 */
export class ProviderGateway {
  readonly registry = new ProviderRegistry();
  private readonly listeners = new Set<ProviderGatewayListener>();
  private started = false;
  private reqSeq = 0;

  start(registerBuiltins = true): void {
    if (this.started) return;
    if (registerBuiltins && this.registry.list().length === 0) {
      for (const p of createBuiltinProviders()) {
        this.registry.register(p);
      }
    }
    this.started = true;
    this.emit("provider.health", this.getStatus());
  }

  stop(): void {
    this.started = false;
  }

  on(listener: ProviderGatewayListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getStatus(): GatewayStatus {
    const snaps = this.registry.snapshots();
    const connected = snaps.filter((s) => s.connected).length;
    const currentRequests = snaps.reduce((n, s) => n + s.currentRequests, 0);
    const down = snaps.filter((s) => s.health.status === "DOWN").length;
    return {
      id: "ados.provider_gateway",
      name: "Provider Gateway",
      health:
        snaps.length === 0
          ? "DOWN"
          : down === snaps.length
            ? "DOWN"
            : down > 0
              ? "DEGRADED"
              : "OK",
      providers: snaps.length,
      connected,
      activeConnections: connected,
      currentRequests,
    };
  }

  listProviders(): ProviderSnapshot[] {
    return this.registry.snapshots();
  }

  capabilities(): Record<string, readonly { id: string; description: string }[]> {
    const out: Record<string, readonly { id: string; description: string }[]> =
      {};
    for (const p of this.registry.list()) {
      out[p.id] = p.capabilities();
    }
    return out;
  }

  async connect(providerId?: string): Promise<ProviderSnapshot[]> {
    const targets = providerId
      ? [this.registry.require(providerId)]
      : [...this.registry.list()];
    for (const p of targets) {
      await p.connect();
      this.emit("provider.connected", p.snapshot());
      this.emit("provider.health", p.health());
    }
    return targets.map((p) => p.snapshot());
  }

  async disconnect(providerId?: string): Promise<ProviderSnapshot[]> {
    const targets = providerId
      ? [this.registry.require(providerId)]
      : [...this.registry.list()];
    for (const p of targets) {
      await p.disconnect();
      this.emit("provider.disconnected", p.snapshot());
      this.emit("provider.health", p.health());
    }
    return targets.map((p) => p.snapshot());
  }

  selectProvider(options: SelectProviderOptions = {}): IProvider {
    if (options.preferredId) {
      return this.registry.require(options.preferredId);
    }
    if (options.preferredAlias) {
      const mapped = aliasToId(options.preferredAlias);
      if (mapped && this.registry.get(mapped)) {
        return this.registry.require(mapped);
      }
    }
    if (options.capability) {
      const byCap = this.registry.findByCapability(options.capability);
      if (byCap) return byCap;
    }
    // Prefer connected local fallback, else first registered
    const local = this.registry.get("provider.local");
    if (local) return local;
    const first = this.registry.list()[0];
    if (!first) throw new Error("No providers registered");
    return first;
  }

  async execute(input: {
    providerId?: string;
    preferredAlias?: string;
    capability: string;
    payload?: unknown;
  }): Promise<ProviderExecuteResult> {
    const provider = this.selectProvider({
      ...(input.providerId !== undefined ? { preferredId: input.providerId } : {}),
      ...(input.preferredAlias !== undefined
        ? { preferredAlias: input.preferredAlias }
        : {}),
      capability: input.capability,
    });

    if (!provider.snapshot().connected) {
      await provider.connect();
      this.emit("provider.connected", provider.snapshot());
    }

    const requestId = this.nextRequestId();
    const result = await provider.execute({
      requestId,
      capability: input.capability,
      input: input.payload ?? {},
      providerId: provider.id,
    });

    if (result.ok) {
      this.emit("provider.execution", result);
    } else {
      this.emit("provider.error", result);
    }
    this.emit("provider.health", provider.health());
    return result;
  }

  aggregateMetrics(): {
    activeConnections: number;
    avgResponseTimeMs: number;
    successes: number;
    errors: number;
    totalRequests: number;
    providers: Record<string, ProviderSnapshot["metrics"]>;
  } {
    const snaps = this.listProviders();
    let successes = 0;
    let errors = 0;
    let totalRequests = 0;
    let weighted = 0;
    const providers: Record<string, ProviderSnapshot["metrics"]> = {};
    for (const s of snaps) {
      providers[s.id] = s.metrics;
      successes += s.metrics.successes;
      errors += s.metrics.errors;
      totalRequests += s.metrics.totalRequests;
      weighted += s.metrics.avgResponseTimeMs * s.metrics.totalRequests;
    }
    return {
      activeConnections: snaps.filter((s) => s.connected).length,
      avgResponseTimeMs:
        totalRequests === 0 ? 0 : Math.round(weighted / totalRequests),
      successes,
      errors,
      totalRequests,
      providers,
    };
  }

  private nextRequestId(): string {
    this.reqSeq += 1;
    return `preq_${Date.now().toString(36)}_${this.reqSeq}`;
  }

  private emit(type: ProviderEventType, payload: unknown): void {
    for (const listener of this.listeners) {
      try {
        listener({ type, payload });
      } catch {
        /* ignore */
      }
    }
  }
}

function aliasToId(alias: string): string | undefined {
  const key = alias.toLowerCase().replace(/^provider\./, "");
  const map: Record<string, string> = {
    cursor: "provider.cursor",
    openai: "provider.openai",
    claude: "provider.claude",
    github: "provider.github",
    local: "provider.local",
    "local-llm": "provider.local",
    telegram: "provider.local",
  };
  return map[key];
}

export function createProviderGateway(): ProviderGateway {
  return new ProviderGateway();
}
