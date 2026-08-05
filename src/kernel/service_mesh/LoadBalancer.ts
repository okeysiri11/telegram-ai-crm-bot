import type { ServiceDescriptor } from "./ServiceDescriptor.js";
import type { ServiceEndpoint } from "./ServiceEndpoint.js";
import type { LoadBalanceStrategy } from "./types.js";

export interface EndpointCandidate {
  readonly service: ServiceDescriptor;
  readonly endpoint: ServiceEndpoint;
}

/**
 * Selects endpoints among healthy candidates.
 */
export class LoadBalancer {
  private rrIndex = 0;
  private readonly strategy: LoadBalanceStrategy;

  constructor(strategy: LoadBalanceStrategy = "priority") {
    this.strategy = strategy;
  }

  select(candidates: readonly EndpointCandidate[]): EndpointCandidate | undefined {
    const healthy = candidates.filter(
      (c) =>
        c.service.status === "healthy" || c.service.status === "degraded",
    );
    const pool = healthy.length > 0 ? healthy : [...candidates];
    if (pool.length === 0) return undefined;

    switch (this.strategy) {
      case "first-healthy":
        return pool[0];
      case "random": {
        const idx = Math.floor(Math.random() * pool.length);
        return pool[idx];
      }
      case "round-robin": {
        const idx = this.rrIndex % pool.length;
        this.rrIndex += 1;
        return pool[idx];
      }
      case "priority":
      default: {
        const sorted = [...pool].sort(
          (a, b) =>
            b.service.priority - a.service.priority ||
            b.endpoint.weight - a.endpoint.weight,
        );
        return sorted[0];
      }
    }
  }

  /** Ordered failover chain excluding the chosen primary. */
  failoverChain(
    candidates: readonly EndpointCandidate[],
    exclude?: EndpointCandidate,
  ): EndpointCandidate[] {
    return [...candidates]
      .filter(
        (c) =>
          !exclude ||
          c.service.id !== exclude.service.id ||
          c.endpoint.id !== exclude.endpoint.id,
      )
      .sort(
        (a, b) =>
          b.service.priority - a.service.priority ||
          b.endpoint.weight - a.endpoint.weight,
      );
  }
}
