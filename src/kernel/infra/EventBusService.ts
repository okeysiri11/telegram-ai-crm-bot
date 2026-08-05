import {
  EventBus as EnterpriseEventBus,
  createEventBus,
} from "../event_bus/EventBus.js";
import type { IEventBus } from "../interfaces/IEventBus.js";
import type { HealthSnapshot } from "../interfaces/types.js";
import { InfrastructureService } from "./InfrastructureService.js";
import { KernelEventBusAdapter } from "../event_bus/KernelEventBusAdapter.js";

export const EVENT_BUS_SERVICE_ID = "ados.event_bus";

/**
 * Event bus as a registry service so HealthMonitor can watch it.
 * Holds the Enterprise Event Bus (communication backbone).
 */
export class EventBusService extends InfrastructureService {
  readonly enterprise: EnterpriseEventBus;
  readonly bus: IEventBus;

  constructor(enterprise?: EnterpriseEventBus) {
    super({
      id: EVENT_BUS_SERVICE_ID,
      kind: "event-bus",
      version: "1.1.0",
      critical: true,
    });
    this.enterprise = enterprise ?? createEventBus();
    this.bus = new KernelEventBusAdapter(this.enterprise);
  }

  override health(): HealthSnapshot {
    const base = super.health();
    const stats = this.enterprise.stats();
    return {
      ...base,
      details: {
        ...base.details,
        transport: "enterprise-in-memory",
        subscriptions: stats.subscriptions,
        historySize: stats.historySize,
        totalPublished: stats.totalPublished,
      },
    };
  }
}
