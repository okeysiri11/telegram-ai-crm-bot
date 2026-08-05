import type { ADOSEvent } from "./types.js";
import { EventFilter } from "./EventFilter.js";
import type { EventFilterCriteria } from "./types.js";

/**
 * Bounded ring-buffer history for replay and audit.
 * O(1) append; supports millions of events with fixed memory via capacity.
 */
export class EventHistory {
  private readonly buffer: (ADOSEvent | undefined)[];
  private readonly capacity: number;
  private writeIndex = 0;
  private size = 0;
  private totalWritten = 0;

  constructor(capacity = 100_000) {
    if (capacity < 1) {
      throw new Error("EventHistory capacity must be >= 1");
    }
    this.capacity = capacity;
    this.buffer = new Array<ADOSEvent | undefined>(capacity);
  }

  get length(): number {
    return this.size;
  }

  get capacityLimit(): number {
    return this.capacity;
  }

  get totalPublished(): number {
    return this.totalWritten;
  }

  append(event: ADOSEvent): void {
    this.buffer[this.writeIndex] = event;
    this.writeIndex = (this.writeIndex + 1) % this.capacity;
    if (this.size < this.capacity) {
      this.size += 1;
    }
    this.totalWritten += 1;
  }

  /** Oldest → newest within the ring. */
  list(criteria?: EventFilterCriteria, limit?: number): ADOSEvent[] {
    const predicate = EventFilter.compile(criteria);
    const out: ADOSEvent[] = [];
    const start =
      this.size < this.capacity
        ? 0
        : this.writeIndex;
    for (let i = 0; i < this.size; i += 1) {
      const idx = (start + i) % this.capacity;
      const event = this.buffer[idx];
      if (!event) continue;
      if (!predicate(event)) continue;
      out.push(event);
      if (limit !== undefined && out.length >= limit) break;
    }
    return out;
  }

  clear(): void {
    this.buffer.fill(undefined);
    this.writeIndex = 0;
    this.size = 0;
  }
}
