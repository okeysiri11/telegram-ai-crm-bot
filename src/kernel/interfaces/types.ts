/**
 * ADOS Kernel shared types.
 * Kernel must never import business verticals (CRM, ERP, Marketplace, …).
 */

/** Lifecycle states for kernel-managed services and the kernel itself. */
export type LifecycleState =
  | "Created"
  | "Initialized"
  | "Started"
  | "Paused"
  | "Stopped"
  | "Disposed";

/** Aggregated / per-service health status. */
export type HealthStatus =
  | "healthy"
  | "degraded"
  | "unhealthy"
  | "unknown"
  | "starting"
  | "stopped";

/** Service identity categories allowed in the kernel registry. */
export type ServiceKind =
  | "infrastructure"
  | "provider-host"
  | "runtime-host"
  | "memory-host"
  | "plugin-host"
  | "event-bus"
  | "kernel"
  | "extension";

export interface HealthSnapshot {
  readonly id: string;
  readonly status: HealthStatus;
  readonly uptimeMs: number;
  readonly version: string;
  readonly checkedAt: string;
  readonly message?: string;
  readonly details?: Readonly<Record<string, unknown>>;
}

export interface PlatformHealthReport {
  readonly status: HealthStatus;
  readonly checkedAt: string;
  readonly services: readonly HealthSnapshot[];
  readonly healthyCount: number;
  readonly degradedCount: number;
  readonly unhealthyCount: number;
}

export interface KernelConfig {
  readonly edition: string;
  readonly environment: "development" | "test" | "production";
  readonly version: string;
  readonly failFast: boolean;
  readonly featureFlags: Readonly<Record<string, boolean>>;
}

export interface ServiceRegistrationOptions {
  readonly replace?: boolean;
}

/** Kernel boot phases (infrastructure only — no business modules). */
export type BootPhase =
  | "load-config"
  | "register-services"
  | "initialize-providers"
  | "initialize-runtime"
  | "initialize-memory"
  | "initialize-plugins"
  | "start-services"
  | "boot-completed";

export interface BootCompletedPayload {
  readonly kernelVersion: string;
  readonly startedAt: string;
  readonly durationMs: number;
  readonly serviceIds: readonly string[];
  readonly config: KernelConfig;
}

export type KernelEventMap = {
  BootCompleted: BootCompletedPayload;
  ServiceRegistered: { id: string; version: string };
  ServiceUnregistered: { id: string };
  LifecycleChanged: { id: string; from: LifecycleState; to: LifecycleState };
  HealthChanged: HealthSnapshot;
};
