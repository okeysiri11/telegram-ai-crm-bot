import type { EventHandler, IEventBus } from "../interfaces/IEventBus.js";
import type { KernelEventMap } from "../interfaces/types.js";
import {
  EventBus as EnterpriseEventBus,
  type EventBus as EnterpriseEventBusType,
} from "./EventBus.js";
import { StandardEventTypes } from "./types.js";

/**
 * Adapts Enterprise EventBus to the Kernel's typed IEventBus (BootCompleted, …)
 * without circular dependencies or business imports.
 */
export class KernelEventBusAdapter implements IEventBus {
  readonly enterprise: EnterpriseEventBusType;

  constructor(enterprise?: EnterpriseEventBusType) {
    this.enterprise = enterprise ?? new EnterpriseEventBus();
  }

  async publish<K extends keyof KernelEventMap>(
    event: K,
    payload: KernelEventMap[K],
  ): Promise<void> {
    const type =
      event === "BootCompleted"
        ? StandardEventTypes.BootCompleted
        : String(event);
    await this.enterprise.publish({
      type,
      payload,
      mode: "sync",
      metadata: { source: "ados.kernel" },
    });
  }

  subscribe<K extends keyof KernelEventMap>(
    event: K,
    handler: EventHandler<KernelEventMap[K]>,
  ): () => void {
    const type =
      event === "BootCompleted"
        ? StandardEventTypes.BootCompleted
        : String(event);
    const sub = this.enterprise.subscribe(type, (adosEvent) => {
      return handler(adosEvent.payload as KernelEventMap[K]);
    });
    return () => {
      sub.unsubscribe();
    };
  }

  clear(): void {
    this.enterprise.clear();
  }
}
