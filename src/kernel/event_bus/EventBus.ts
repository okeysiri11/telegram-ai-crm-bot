import { Event } from "./Event.js";
import { EventDispatcher } from "./EventDispatcher.js";
import { EventFilter } from "./EventFilter.js";
import { EventHistory } from "./EventHistory.js";
import { EventPublisher } from "./EventPublisher.js";
import { EventRegistry } from "./EventRegistry.js";
import { EventSubscriber } from "./EventSubscriber.js";
import type {
  ADOSEvent,
  EventBusOptions,
  EventHandler,
  EventInput,
  ReplayOptions,
  SubscribeOptions,
  Subscription,
} from "./types.js";

/**
 * Async mutex — serializes critical publish/dispatch sections under concurrent awaits.
 */
class AsyncMutex {
  private chain: Promise<void> = Promise.resolve();

  run<T>(fn: () => Promise<T>): Promise<T> {
    const next = this.chain.then(fn, fn);
    this.chain = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  }
}

/**
 * ADOS Enterprise Event Bus — communication backbone.
 *
 * Kernel → Event Bus → Runtime → Agents → Business Modules
 * Business modules never communicate directly.
 */
export class EventBus {
  readonly registry: EventRegistry;
  readonly history: EventHistory;
  readonly subscriber: EventSubscriber;
  readonly dispatcher: EventDispatcher;
  readonly publisher: EventPublisher;

  private readonly mutex = new AsyncMutex();
  private readonly delayedTimers = new Map<
    string,
    ReturnType<typeof setTimeout>
  >();
  private readonly maxDelayed: number;
  private disposed = false;

  constructor(options?: EventBusOptions) {
    this.registry = new EventRegistry(true);
    this.history = new EventHistory(options?.history?.capacity ?? 100_000);
    this.subscriber = new EventSubscriber();
    this.dispatcher = new EventDispatcher();
    this.maxDelayed = options?.maxDelayed ?? 100_000;

    this.publisher = new EventPublisher(this.registry, this.history, {
      onDispatch: (event) => this.routeDispatch(event),
      scheduleDelayed: (event, delayMs) =>
        this.scheduleDelayed(event, delayMs),
    });
  }

  async publish<TPayload = unknown>(
    event: EventInput<TPayload> | ADOSEvent<TPayload>,
  ): Promise<ADOSEvent<TPayload>> {
    this.assertActive();
    return this.publisher.publish(event);
  }

  async broadcast<TPayload = unknown>(
    event: EventInput<TPayload>,
  ): Promise<ADOSEvent<TPayload>> {
    this.assertActive();
    const published = await this.publisher.publish({
      ...event,
      metadata: {
        ...(event.metadata ?? {}),
        broadcast: true,
      },
    });
    // Additionally notify every subscriber (cross-cutting broadcast)
    await this.mutex.run(async () => {
      const all = this.subscriber.collectAll();
      // Avoid double-delivery to those who already matched type
      const already = new Set(
        this.subscriber.collect(published.type).map((s) => s.id),
      );
      const extras = all.filter((s) => !already.has(s.id));
      if (extras.length > 0) {
        await this.dispatcher.dispatch(published, extras);
      }
    });
    return published;
  }

  subscribe(
    eventType: string,
    handler: EventHandler,
    options?: SubscribeOptions,
  ): Subscription {
    this.assertActive();
    const sub = this.subscriber.subscribe(eventType, handler, options);

    if (!eventType.includes("*")) {
      const sticky = this.registry.getSticky(eventType);
      if (sticky) {
        const filter = options?.filter;
        if (!filter || filter(sticky)) {
          void Promise.resolve(handler(sticky)).catch(() => undefined);
          if (options?.once === true) {
            sub.unsubscribe();
          }
        }
      }
    }

    return sub;
  }

  unsubscribe(subscriptionId: string): boolean {
    return this.subscriber.unsubscribe(subscriptionId);
  }

  unsubscribeHandler(eventType: string, handler: EventHandler): number {
    return this.subscriber.unsubscribeHandler(eventType, handler);
  }

  once(
    eventType: string,
    handler: EventHandler,
    options?: Omit<SubscribeOptions, "once">,
  ): Subscription {
    return this.subscribe(eventType, handler, { ...options, once: true });
  }

  async replay(options?: ReplayOptions): Promise<number> {
    this.assertActive();
    const events = this.history.list(options?.filter, options?.limit);
    if (options?.dispatch === false) {
      return events.length;
    }
    for (const event of events) {
      await this.dispatchToSubscribers(event);
    }
    return events.length;
  }

  getHistory(
    filter?: ReplayOptions["filter"],
    limit?: number,
  ): readonly ADOSEvent[] {
    return this.history.list(filter, limit);
  }

  clearHistory(): void {
    this.history.clear();
  }

  stats(): {
    subscriptions: number;
    historySize: number;
    historyCapacity: number;
    totalPublished: number;
    delayedPending: number;
    registeredTypes: number;
  } {
    return {
      subscriptions: this.subscriber.count(),
      historySize: this.history.length,
      historyCapacity: this.history.capacityLimit,
      totalPublished: this.history.totalPublished,
      delayedPending: this.delayedTimers.size,
      registeredTypes: this.registry.list().length,
    };
  }

  matchesFilter(
    event: ADOSEvent,
    criteria: NonNullable<ReplayOptions["filter"]>,
  ): boolean {
    return EventFilter.compile(criteria)(event);
  }

  async dispose(): Promise<void> {
    this.disposed = true;
    for (const timer of this.delayedTimers.values()) {
      clearTimeout(timer);
    }
    this.delayedTimers.clear();
    this.subscriber.clear();
    this.registry.clearSticky();
  }

  clear(): void {
    this.subscriber.clear();
    this.history.clear();
    this.registry.clearSticky();
    for (const timer of this.delayedTimers.values()) {
      clearTimeout(timer);
    }
    this.delayedTimers.clear();
  }

  private assertActive(): void {
    if (this.disposed) {
      throw new Error("EventBus is disposed");
    }
  }

  private async scheduleDelayed(
    event: ADOSEvent,
    delayMs: number,
  ): Promise<string> {
    if (this.delayedTimers.size >= this.maxDelayed) {
      throw new Error("EventBus delayed queue is full");
    }
    return new Promise<string>((resolve) => {
      const timer = setTimeout(() => {
        this.delayedTimers.delete(event.id);
        // Deliver without holding an outer mutex — dispatchToSubscribers locks once.
        void this.publisher.deliver({
          ...event,
          mode: "sync",
        });
      }, delayMs);
      this.delayedTimers.set(event.id, timer);
      resolve(event.id);
    });
  }

  private async routeDispatch(event: ADOSEvent): Promise<void> {
    if (event.mode === "async") {
      // Schedule dispatch; resolve after enqueue for high throughput
      await new Promise<void>((resolve) => {
        queueMicrotask(() => {
          void this.dispatchToSubscribers(event).finally(() => undefined);
          resolve();
        });
      });
      return;
    }
    // sync (and delayed-after-fire)
    await this.dispatchToSubscribers(event);
  }

  private async dispatchToSubscribers(event: ADOSEvent): Promise<void> {
    await this.mutex.run(async () => {
      const list = this.subscriber.collect(event.type);
      const result = await this.dispatcher.dispatch(event, list);
      for (const id of result.onceDeliveredIds) {
        this.subscriber.unsubscribe(id);
      }
    });
  }
}

export function createEventBus(options?: EventBusOptions): EventBus {
  return new EventBus(options);
}

export { Event };
