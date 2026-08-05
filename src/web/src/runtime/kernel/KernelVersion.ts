/**
 * Kernel version & platform identity — Sprint 29.9.
 */

export const KERNEL_RUNTIME_VERSION = "29.9";
export const KERNEL_PERSIST_KEY = "ews_kernel_runtime_v1";
export const KERNEL_API_PREFIX = "/api/enterprise-kernel/v1";

export const PLATFORM_IDENTITY = {
  name: "ADOS Enterprise Platform",
  application: "enterprise_web_platform",
  kernelVersion: KERNEL_RUNTIME_VERSION,
  /** Compatible orchestrator sprint */
  orchestratorVersion: "29.8",
  minRuntimeSprint: "29.0",
} as const;

export const kernelVersion = {
  current: KERNEL_RUNTIME_VERSION,
  platform: PLATFORM_IDENTITY,
  matches(expected: string) {
    return expected === KERNEL_RUNTIME_VERSION || expected.startsWith("29.");
  },
  descriptor() {
    return {
      kernel: KERNEL_RUNTIME_VERSION,
      platform: PLATFORM_IDENTITY.name,
      application: PLATFORM_IDENTITY.application,
      orchestrator: PLATFORM_IDENTITY.orchestratorVersion,
    };
  },
};
