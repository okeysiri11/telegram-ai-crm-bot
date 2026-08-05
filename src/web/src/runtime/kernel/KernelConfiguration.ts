/**
 * Kernel configuration · feature flags · license hooks — Sprint 29.9.
 */

import { webConfig } from "@/config/webConfig";
import { KERNEL_RUNTIME_VERSION } from "./KernelVersion";
import type { FeatureFlags, KernelConfig, LicenseHookResult } from "./kernelTypes";
import { publishKernelEvent } from "./kernelEvents";

function now() {
  return new Date().toISOString();
}

function defaultFlags(): FeatureFlags {
  return {
    orchestratorEnabled: true,
    recoveryEnabled: true,
    diagnosticsEnabled: true,
    licenseHooksEnabled: true,
    backgroundHealthProbe: true,
    safeRestart: true,
  };
}

let config: KernelConfig | null = null;
const flagOverrides = new Map<keyof FeatureFlags, boolean>();

export const kernelConfiguration = {
  clear() {
    config = null;
    flagOverrides.clear();
  },

  /** Load configuration (orchestration only — no business rules). */
  load(envHint?: KernelConfig["environment"]): KernelConfig {
    const environment: KernelConfig["environment"] =
      envHint ||
      (import.meta.env.MODE === "test"
        ? "test"
        : import.meta.env.PROD
          ? "production"
          : "development");

    const license = this.verifyLicenseHooks();
    const featureFlags = { ...defaultFlags() };
    for (const [k, v] of flagOverrides) featureFlags[k] = v;

    config = {
      version: KERNEL_RUNTIME_VERSION,
      environment,
      featureFlags,
      bootTimeoutMs: environment === "test" ? 30_000 : 60_000,
      recoveryMaxAttempts: 2,
      healthProbeIntervalMs: environment === "test" ? 60_000 : 20_000,
      license: {
        verified: license.ok,
        mode: license.mode,
        message: license.message,
      },
      loadedAt: now(),
    };
    publishKernelEvent("ConfigLoaded", {
      environment: config.environment,
      licenseMode: config.license.mode,
    });
    return this.get();
  },

  get(): KernelConfig {
    if (!config) return this.load();
    return {
      ...config,
      featureFlags: { ...config.featureFlags },
      license: { ...config.license },
    };
  },

  setFeatureFlag(flag: keyof FeatureFlags, enabled: boolean) {
    flagOverrides.set(flag, enabled);
    if (config) {
      config = {
        ...config,
        featureFlags: { ...config.featureFlags, [flag]: enabled },
      };
    }
    publishKernelEvent("FeatureFlagChanged", { flag, enabled });
    return this.get().featureFlags;
  },

  /**
   * License verification hooks — placeholder for future enterprise licensing.
   * Never blocks demo/dev boot; records hook result only.
   */
  verifyLicenseHooks(): LicenseHookResult {
    const demo = Boolean(webConfig.demoAuthEnabled);
    const result: LicenseHookResult = {
      ok: true,
      mode: demo ? "demo" : import.meta.env.PROD ? "enterprise" : "dev",
      message: demo
        ? "Demo license hook accepted"
        : "License hook placeholder — verified for local kernel",
      checkedAt: now(),
    };
    publishKernelEvent("LicenseHookChecked", {
      ok: result.ok,
      mode: result.mode,
    });
    return result;
  },

  problems(): string[] {
    const c = this.get();
    const problems: string[] = [];
    if (!c.featureFlags.orchestratorEnabled) {
      problems.push("orchestrator_disabled");
    }
    if (c.featureFlags.licenseHooksEnabled && !c.license.verified) {
      problems.push("license_unverified");
    }
    if (c.bootTimeoutMs < 1000) {
      problems.push("boot_timeout_too_low");
    }
    return problems;
  },
};
