import type { IServiceRegistry } from "./IServiceRegistry.js";
import type { BootPhase, KernelConfig } from "./types.js";
import type { EventBus as EnterpriseEventBus } from "../event_bus/EventBus.js";

export interface BootLoaderContext {
  readonly registry: IServiceRegistry;
  readonly config: KernelConfig;
  /** Shared enterprise event bus instance (communication backbone). */
  readonly enterpriseEventBus?: EnterpriseEventBus;
}

/**
 * Executes the infrastructure boot sequence.
 * Loads providers/runtime/memory/plugins hosts — never business verticals.
 */
export interface IBootLoader {
  readonly phasesCompleted: readonly BootPhase[];
  boot(context: BootLoaderContext): Promise<void>;
}
