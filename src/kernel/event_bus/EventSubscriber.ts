import type {
  EventHandler,
  EventFilterFn,
  EventPriority,
  SubscribeOptions,
  Subscription,
} from "./types.js";

export interface SubscriberRecord {
  readonly id: string;
  readonly eventType: string;
  readonly handler: EventHandler;
  readonly priority: EventPriority;
  readonly once: boolean;
  readonly filter?: EventFilterFn;
  readonly async: boolean;
  active: boolean;
}

let subSeq = 0;

function nextSubId(): string {
  subSeq += 1;
  return `sub_${subSeq.toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Manages subscription records for one or more event type patterns.
 */
export class EventSubscriber {
  private readonly byId = new Map<string, SubscriberRecord>();
  /** Exact type → subscribers */
  private readonly byType = new Map<string, SubscriberRecord[]>();
  /** Wildcard patterns */
  private readonly wildcards: SubscriberRecord[] = [];

  subscribe(
    eventType: string,
    handler: EventHandler,
    options?: SubscribeOptions,
  ): Subscription {
    const record: SubscriberRecord = {
      id: nextSubId(),
      eventType,
      handler,
      priority: options?.priority ?? 0,
      once: options?.once === true,
      ...(options?.filter !== undefined ? { filter: options.filter } : {}),
      async: options?.async === true,
      active: true,
    };

    this.byId.set(record.id, record);
    if (eventType.includes("*")) {
      this.wildcards.push(record);
      this.sortList(this.wildcards);
    } else {
      const list = this.byType.get(eventType) ?? [];
      list.push(record);
      this.sortList(list);
      this.byType.set(eventType, list);
    }

    return {
      id: record.id,
      eventType,
      priority: record.priority,
      once: record.once,
      unsubscribe: () => {
        this.unsubscribe(record.id);
      },
    };
  }

  once(
    eventType: string,
    handler: EventHandler,
    options?: Omit<SubscribeOptions, "once">,
  ): Subscription {
    return this.subscribe(eventType, handler, { ...options, once: true });
  }

  unsubscribe(subscriptionId: string): boolean {
    const record = this.byId.get(subscriptionId);
    if (!record) {
      return false;
    }
    record.active = false;
    this.byId.delete(subscriptionId);
    this.removeFromLists(record);
    return true;
  }

  unsubscribeHandler(eventType: string, handler: EventHandler): number {
    let removed = 0;
    for (const [id, record] of [...this.byId]) {
      if (record.eventType === eventType && record.handler === handler) {
        this.unsubscribe(id);
        removed += 1;
      }
    }
    return removed;
  }

  /**
   * Snapshot of matching subscribers (priority desc). Safe during dispatch.
   */
  collect(eventType: string): readonly SubscriberRecord[] {
    const exact = this.byType.get(eventType) ?? [];
    const wild = this.wildcards.filter((r) => r.active);
    const matchedWild = wild.filter((r) =>
      matchesPattern(r.eventType, eventType),
    );
    const merged = [...exact.filter((r) => r.active), ...matchedWild];
    this.sortList(merged);
    return merged;
  }

  /** All active subscribers (for broadcast). */
  collectAll(): readonly SubscriberRecord[] {
    const merged = [...this.byId.values()].filter((r) => r.active);
    this.sortList(merged);
    return merged;
  }

  count(): number {
    return this.byId.size;
  }

  clear(): void {
    this.byId.clear();
    this.byType.clear();
    this.wildcards.length = 0;
  }

  private removeFromLists(record: SubscriberRecord): void {
    if (record.eventType.includes("*")) {
      const idx = this.wildcards.indexOf(record);
      if (idx >= 0) this.wildcards.splice(idx, 1);
      return;
    }
    const list = this.byType.get(record.eventType);
    if (!list) return;
    const idx = list.indexOf(record);
    if (idx >= 0) list.splice(idx, 1);
    if (list.length === 0) this.byType.delete(record.eventType);
  }

  private sortList(list: SubscriberRecord[]): void {
    list.sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));
  }
}

function matchesPattern(pattern: string, eventType: string): boolean {
  if (pattern === "*" || pattern === "**") return true;
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`).test(eventType);
}
