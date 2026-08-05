import type { IBootLoader } from "./IBootLoader.js";
import type { IEventBus } from "./IEventBus.js";
import type { IHealthMonitor } from "./IHealthMonitor.js";
import type { IServiceRegistry } from "./IServiceRegistry.js";
import type { KernelConfig, LifecycleState, PlatformHealthReport } from "./types.js";
import type { IServiceMesh } from "../service_mesh/interfaces.js";
import type { IWorkflowEngine } from "../workflow/interfaces.js";

/**
 * Single entry point for ADOS OS kernel.
 * Must not import CRM, ERP, Marketplace, AI Studio, or other verticals.
 */
export interface IKernel {
  readonly version: string;
  readonly config: KernelConfig;
  readonly registry: IServiceRegistry;
  readonly healthMonitor: IHealthMonitor;
  readonly eventBus: IEventBus;
  readonly bootLoader: IBootLoader;
  readonly serviceMesh: IServiceMesh;
  readonly workflowEngine: IWorkflowEngine;

  getState(): LifecycleState;
  start(configOverrides?: Partial<KernelConfig>): Promise<void>;
  stop(): Promise<void>;
  dispose(): Promise<void>;
  getHealth(): Promise<PlatformHealthReport>;
}
