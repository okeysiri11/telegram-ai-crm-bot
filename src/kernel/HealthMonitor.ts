import type { IHealthMonitor } from "./interfaces/IHealthMonitor.js";
import type { IService } from "./interfaces/IService.js";
import type {
  HealthSnapshot,
  HealthStatus,
  PlatformHealthReport,
} from "./interfaces/types.js";

function rank(status: HealthStatus): number {
  switch (status) {
    case "unhealthy":
      return 5;
    case "unknown":
      return 4;
    case "starting":
      return 3;
    case "degraded":
      return 2;
    case "stopped":
      return 1;
    case "healthy":
      return 0;
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

function worst(
  statuses: readonly HealthStatus[],
): HealthStatus {
  if (statuses.length === 0) {
    return "unknown";
  }
  return statuses.reduce((a, b) => (rank(b) > rank(a) ? b : a));
}

/**
 * Aggregates health() from every watched service.
 */
export class HealthMonitor implements IHealthMonitor {
  private readonly watched = new Map<string, IService>();
  private readonly cache = new Map<string, HealthSnapshot>();

  watch(service: IService): void {
    this.watched.set(service.id, service);
  }

  unwatch(id: string): void {
    this.watched.delete(id);
    this.cache.delete(id);
  }

  async check(id: string): Promise<HealthSnapshot> {
    const service = this.watched.get(id);
    if (!service) {
      throw new Error(`HealthMonitor is not watching service: ${id}`);
    }
    const snapshot = await Promise.resolve(service.health());
    this.cache.set(id, snapshot);
    return snapshot;
  }

  async report(): Promise<PlatformHealthReport> {
    const services: HealthSnapshot[] = [];
    for (const id of this.watched.keys()) {
      services.push(await this.check(id));
    }

    let healthyCount = 0;
    let degradedCount = 0;
    let unhealthyCount = 0;
    for (const s of services) {
      if (s.status === "healthy") healthyCount += 1;
      else if (s.status === "degraded") degradedCount += 1;
      else if (s.status === "unhealthy" || s.status === "unknown") {
        unhealthyCount += 1;
      }
    }

    return {
      status: worst(services.map((s) => s.status)),
      checkedAt: new Date().toISOString(),
      services: Object.freeze(services),
      healthyCount,
      degradedCount,
      unhealthyCount,
    };
  }

  getCached(id: string): HealthSnapshot | undefined {
    return this.cache.get(id);
  }

  clear(): void {
    this.watched.clear();
    this.cache.clear();
  }
}
