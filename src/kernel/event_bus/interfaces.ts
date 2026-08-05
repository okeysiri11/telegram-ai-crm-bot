import type {
  ADOSEvent,
  EventBusOptions,
  EventHandler,
  EventInput,
  ReplayOptions,
  SubscribeOptions,
  Subscription,
} from "./types.js";
import type { EventRegistry } from "./EventRegistry.js";
import type { EventHistory } from "./EventHistory.js";

/**
 * DI-facing contract for the Enterprise Event Bus.
 * Plugins/Runtime/Modules depend on this interface — not concrete class.
 */
export interface IEnterpriseEventBus {
  publish<TPayload = unknown>(
    event: EventInput<TPayload> | ADOSEvent<TPayload>,
  ): Promise<ADOSEvent<TPayload>>;
  broadcast<TPayload = unknown>(
    event: EventInput<TPayload>,
  ): Promise<ADOSEvent<TPayload>>;
  subscribe(
    eventType: string,
    handler: EventHandler,
    options?: SubscribeOptions,
  ): Subscription;
  unsubscribe(subscriptionId: string): boolean;
  once(
    eventType: string,
    handler: EventHandler,
    options?: Omit<SubscribeOptions, "once">,
  ): Subscription;
  replay(options?: ReplayOptions): Promise<number>;
  getHistory(
    filter?: ReplayOptions["filter"],
    limit?: number,
  ): readonly ADOSEvent[];
  clear(): void;
  dispose(): Promise<void>;
  readonly registry: EventRegistry;
  readonly history: EventHistory;
  stats(): {
    subscriptions: number;
    historySize: number;
    historyCapacity: number;
    totalPublished: number;
    delayedPending: number;
    registeredTypes: number;
  };
}

export type { EventBusOptions };
