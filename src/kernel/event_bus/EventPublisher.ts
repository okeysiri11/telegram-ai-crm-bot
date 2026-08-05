import { Event } from "./Event.js";
import type { EventHistory } from "./EventHistory.js";
import type { EventRegistry } from "./EventRegistry.js";
import type { ADOSEvent, EventInput } from "./types.js";

export interface PublisherHooks {
  readonly onDispatch: (event: ADOSEvent) => Promise<void>;
  readonly scheduleDelayed: (
    event: ADOSEvent,
    delayMs: number,
  ) => Promise<string>;
}

/**
 * Publishes events onto the bus — used by Kernel, Runtime, Agents, Modules.
 */
export class EventPublisher {
  constructor(
    private readonly registry: EventRegistry,
    private readonly history: EventHistory,
    private readonly hooks: PublisherHooks,
  ) {}

  async publish<TPayload = unknown>(
    input: EventInput<TPayload> | ADOSEvent<TPayload>,
  ): Promise<ADOSEvent<TPayload>> {
    const event =
      "sequence" in input && "timestamp" in input
        ? Event.fromExisting(input as ADOSEvent<TPayload>)
        : Event.create(input as EventInput<TPayload>);

    this.registry.ensureKnown(event.type);

    if (event.mode === "delayed") {
      await this.hooks.scheduleDelayed(event, event.delayMs);
      return event;
    }

    await this.deliver(event);
    return event;
  }

  async broadcast<TPayload = unknown>(
    input: Omit<EventInput<TPayload>, "type"> & { type?: string },
  ): Promise<ADOSEvent<TPayload>> {
    return this.publish({
      ...input,
      type: input.type ?? "SystemBroadcast",
      metadata: {
        ...(input.metadata ?? {}),
        broadcast: true,
      },
    } as EventInput<TPayload>);
  }

  async deliver(event: ADOSEvent): Promise<void> {
    this.history.append(event);
    if (event.sticky) {
      this.registry.setSticky(event);
    }
    await this.hooks.onDispatch(event);
  }
}
