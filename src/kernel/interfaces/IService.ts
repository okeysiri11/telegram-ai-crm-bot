import type { HealthSnapshot, LifecycleState, ServiceKind } from "./types.js";

/**
 * Contract every kernel-managed service must implement.
 * Future plugins register implementations of this interface.
 */
export interface IService {
  readonly id: string;
  readonly version: string;
  readonly kind: ServiceKind;

  /** Current lifecycle state. */
  getLifecycleState(): LifecycleState;

  /** Health probe — required for HealthMonitor aggregation. */
  health(): HealthSnapshot | Promise<HealthSnapshot>;

  /** Milliseconds since the service entered Started (0 if never started). */
  uptimeMs(): number;

  initialize(): void | Promise<void>;
  start(): void | Promise<void>;
  pause?(): void | Promise<void>;
  stop(): void | Promise<void>;
  dispose(): void | Promise<void>;
}
