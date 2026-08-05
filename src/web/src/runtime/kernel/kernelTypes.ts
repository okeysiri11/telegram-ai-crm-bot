/**
 * Kernel types — Sprint 29.9.
 */

import type { RuntimeId, RuntimeHealthStatus } from "@/runtime/orchestrator";

export type KernelPhase =
  | "uninitialized"
  | "booting"
  | "configuration"
  | "registry"
  | "dependency_validation"
  | "orchestrator_startup"
  | "runtime_startup"
  | "health_validation"
  | "ready"
  | "degraded"
  | "shutting_down"
  | "stopped"
  | "recovering"
  | "restarting"
  | "error";

export type KernelEventName =
  | "BootStarted"
  | "BootCompleted"
  | "PhaseChanged"
  | "ShutdownStarted"
  | "ShutdownCompleted"
  | "RestartRequested"
  | "RecoveryAttempted"
  | "RecoverySucceeded"
  | "RecoveryFailed"
  | "HealthUpdated"
  | "DiagnosticsCollected"
  | "ConfigLoaded"
  | "FeatureFlagChanged"
  | "LicenseHookChecked";

export type BootStepId =
  | "boot"
  | "configuration"
  | "runtime_registry"
  | "dependency_validation"
  | "orchestrator_startup"
  | "all_runtime_startup"
  | "health_validation"
  | "platform_ready";

export type BootStep = {
  id: BootStepId;
  label: string;
  status: "pending" | "running" | "ok" | "failed" | "skipped";
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
  message?: string;
  error?: string;
};

export type FeatureFlags = {
  orchestratorEnabled: boolean;
  recoveryEnabled: boolean;
  diagnosticsEnabled: boolean;
  licenseHooksEnabled: boolean;
  backgroundHealthProbe: boolean;
  safeRestart: boolean;
};

export type KernelConfig = {
  version: string;
  environment: "development" | "staging" | "production" | "test";
  featureFlags: FeatureFlags;
  bootTimeoutMs: number;
  recoveryMaxAttempts: number;
  healthProbeIntervalMs: number;
  license: {
    verified: boolean;
    mode: "dev" | "demo" | "enterprise" | "unknown";
    message?: string;
  };
  loadedAt: string;
};

export type KernelHealthSnapshot = {
  phase: KernelPhase;
  platformStatus: RuntimeHealthStatus | "unknown";
  ready: boolean;
  degraded: boolean;
  runtimeHealthy: number;
  runtimeTotal: number;
  runtimeError: number;
  eventBusOk: boolean;
  checkedAt: string;
};

export type DiagnosticReport = {
  id: string;
  at: string;
  phase: KernelPhase;
  startupTimeMs: number | null;
  memory: {
    usedJsHeapMb?: number;
    totalJsHeapMb?: number;
    limitJsHeapMb?: number;
    available: boolean;
  };
  runtimes: {
    id: string;
    status: string;
    version: string;
  }[];
  failedModules: string[];
  dependencyErrors: string[];
  versionMismatches: string[];
  configurationProblems: string[];
  eventBus: {
    ok: boolean;
    recentErrors: number;
  };
  notes: string[];
};

export type RecoveryRecord = {
  id: string;
  at: string;
  runtimeId?: RuntimeId | string;
  action: "restart" | "mark_unhealthy" | "notify_orchestrator" | "platform_continue";
  ok: boolean;
  attempt: number;
  message: string;
};

export type LicenseHookResult = {
  ok: boolean;
  mode: KernelConfig["license"]["mode"];
  message: string;
  checkedAt: string;
};
