import type { ADOSEvent } from "./types.js";
import type { SubscriberRecord } from "./EventSubscriber.js";

export interface DispatchResult {
  readonly delivered: number;
  readonly failed: number;
  readonly onceDeliveredIds: readonly string[];
  readonly errors: readonly { subscriptionId: string; error: unknown }[];
}

/**
 * Delivers an event to a snapshot of subscribers by priority.
 */
export class EventDispatcher {
  async dispatch(
    event: ADOSEvent,
    subscribers: readonly SubscriberRecord[],
  ): Promise<DispatchResult> {
    let delivered = 0;
    let failed = 0;
    const errors: { subscriptionId: string; error: unknown }[] = [];
    const onceDeliveredIds: string[] = [];

    for (const sub of subscribers) {
      if (!sub.active) continue;
      if (sub.filter && !sub.filter(event)) continue;

      try {
        if (sub.async) {
          void Promise.resolve(sub.handler(event)).catch(() => undefined);
          delivered += 1;
          if (sub.once) onceDeliveredIds.push(sub.id);
        } else {
          await Promise.resolve(sub.handler(event));
          delivered += 1;
          if (sub.once) onceDeliveredIds.push(sub.id);
        }
      } catch (error) {
        failed += 1;
        errors.push({ subscriptionId: sub.id, error });
      }
    }

    return {
      delivered,
      failed,
      onceDeliveredIds: Object.freeze(onceDeliveredIds),
      errors: Object.freeze(errors),
    };
  }
}
