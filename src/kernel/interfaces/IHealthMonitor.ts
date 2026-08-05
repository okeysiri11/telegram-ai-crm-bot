import type { IService } from "./IService.js";
import type { HealthSnapshot, PlatformHealthReport } from "./types.js";

export interface IHealthMonitor {
  /** Register a service for continuous health tracking. */
  watch(service: IService): void;
  unwatch(id: string): void;
  /** Probe one service (live call to health()). */
  check(id: string): Promise<HealthSnapshot>;
  /** Aggregate platform health across watched services. */
  report(): Promise<PlatformHealthReport>;
  /** Last cached snapshot if available. */
  getCached(id: string): HealthSnapshot | undefined;
  clear(): void;
}
