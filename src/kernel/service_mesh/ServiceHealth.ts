import type { IServiceDiscovery, IServiceHealth } from "./interfaces.js";
import type { HeartbeatRecord, MeshHealthStatus } from "./types.js";

/**
 * Health reporting, heartbeats, and timeout detection.
 */
export class ServiceHealth implements IServiceHealth {
  private readonly heartbeats = new Map<string, HeartbeatRecord>();
  private readonly watched = new Set<string>();
  private readonly startedAt = new Map<string, number>();
  private readonly timeoutMs: number;

  constructor(
    private readonly discovery: IServiceDiscovery,
    timeoutMs = 30_000,
  ) {
    this.timeoutMs = timeoutMs;
  }

  watch(serviceId: string): void {
    this.watched.add(serviceId);
    if (!this.startedAt.has(serviceId)) {
      this.startedAt.set(serviceId, Date.now());
    }
  }

  unwatch(serviceId: string): void {
    this.watched.delete(serviceId);
    this.heartbeats.delete(serviceId);
    this.startedAt.delete(serviceId);
  }

  report(
    serviceId: string,
    status: MeshHealthStatus,
    _details?: Record<string, unknown>,
  ): void {
    const desc = this.discovery.get(serviceId);
    if (desc) {
      desc.setStatus(status);
    }
    this.heartbeat(serviceId, status);
  }

  heartbeat(
    serviceId: string,
    status?: MeshHealthStatus,
  ): HeartbeatRecord {
    const desc = this.discovery.get(serviceId);
    const nextStatus = status ?? desc?.status ?? "unknown";
    if (desc && status) {
      desc.setStatus(status);
    }
    const start = this.startedAt.get(serviceId) ?? Date.now();
    if (!this.startedAt.has(serviceId)) {
      this.startedAt.set(serviceId, start);
    }
    const record: HeartbeatRecord = {
      serviceId,
      at: new Date().toISOString(),
      status: nextStatus,
      uptimeMs: Date.now() - start,
    };
    this.heartbeats.set(serviceId, record);
    this.watched.add(serviceId);
    return record;
  }

  getStatus(serviceId: string): MeshHealthStatus {
    return (
      this.discovery.get(serviceId)?.status ??
      this.heartbeats.get(serviceId)?.status ??
      "unknown"
    );
  }

  getHeartbeat(serviceId: string): HeartbeatRecord | undefined {
    return this.heartbeats.get(serviceId);
  }

  checkTimeouts(now = Date.now()): readonly string[] {
    const timedOut: string[] = [];
    for (const serviceId of this.watched) {
      const hb = this.heartbeats.get(serviceId);
      if (!hb) {
        timedOut.push(serviceId);
        this.report(serviceId, "unknown");
        continue;
      }
      const age = now - Date.parse(hb.at);
      if (age > this.timeoutMs) {
        timedOut.push(serviceId);
        this.report(serviceId, "unhealthy");
      }
    }
    return Object.freeze(timedOut);
  }

  clear(): void {
    this.heartbeats.clear();
    this.watched.clear();
    this.startedAt.clear();
  }
}
