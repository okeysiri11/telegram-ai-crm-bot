/**
 * Enterprise Kernel public API — Sprint 29.9.
 */

export {
  KERNEL_RUNTIME_VERSION,
  KERNEL_PERSIST_KEY,
  KERNEL_API_PREFIX,
  PLATFORM_IDENTITY,
  kernelVersion,
} from "./KernelVersion";
export type {
  KernelPhase,
  KernelEventName,
  BootStepId,
  BootStep,
  FeatureFlags,
  KernelConfig,
  KernelHealthSnapshot,
  DiagnosticReport,
  RecoveryRecord,
  LicenseHookResult,
} from "./kernelTypes";

export { kernelEvents, publishKernelEvent } from "./kernelEvents";
export { kernelConfiguration } from "./KernelConfiguration";
export { kernelLifecycle } from "./KernelLifecycle";
export { kernelRegistry } from "./KernelRegistry";
export type { KernelModuleRecord } from "./KernelRegistry";
export { kernelHealth } from "./KernelHealth";
export { kernelDiagnostics } from "./KernelDiagnostics";
export { kernelRecovery } from "./KernelRecovery";
export { kernelBootstrap } from "./KernelBootstrap";
export type { BootstrapResult } from "./KernelBootstrap";
export { enterpriseKernel } from "./EnterpriseKernel";
export { kernelApi, kernelApiPrefix } from "./kernelApi";
