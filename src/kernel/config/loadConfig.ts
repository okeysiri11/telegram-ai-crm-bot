import type { KernelConfig } from "../interfaces/types.js";

export const KERNEL_VERSION = "1.4.0";

export function createDefaultConfig(
  overrides?: Partial<KernelConfig>,
): KernelConfig {
  return {
    edition: overrides?.edition ?? "enterprise",
    environment: overrides?.environment ?? "development",
    version: overrides?.version ?? KERNEL_VERSION,
    failFast: overrides?.failFast ?? true,
    featureFlags: Object.freeze({
      plugins: true,
      providers: true,
      runtime: true,
      memory: true,
      ...(overrides?.featureFlags ?? {}),
    }),
  };
}

/**
 * Load kernel configuration. Intentionally env-light and secret-free.
 * Business module config is out of scope for the kernel.
 */
export function loadKernelConfig(
  overrides?: Partial<KernelConfig>,
): KernelConfig {
  const envName = process.env["ADOS_ENV"];
  const environment =
    envName === "production" || envName === "test" || envName === "development"
      ? envName
      : undefined;

  return createDefaultConfig({
    ...overrides,
    ...(environment !== undefined ? { environment } : {}),
    ...(process.env["ADOS_EDITION"]
      ? { edition: process.env["ADOS_EDITION"] }
      : {}),
  });
}
