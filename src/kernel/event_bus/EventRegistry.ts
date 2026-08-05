import type { ADOSEvent, StandardEventType } from "./types.js";
import { StandardEventTypes } from "./types.js";

export interface RegisteredEventType {
  readonly type: string;
  readonly description?: string;
  readonly stickyDefault?: boolean;
  readonly registeredAt: string;
}

/**
 * Catalog of known event types — DI/plugin ready.
 * Business modules register types here; they never call each other directly.
 */
export class EventRegistry {
  private readonly types = new Map<string, RegisteredEventType>();

  constructor(registerDefaults = true) {
    if (registerDefaults) {
      for (const type of Object.values(StandardEventTypes)) {
        this.register(type, { description: `Standard ADOS event: ${type}` });
      }
    }
  }

  register(
    type: string,
    options?: { description?: string; stickyDefault?: boolean },
  ): void {
    if (!type || type.includes(" ")) {
      throw new Error(`Invalid event type: ${type}`);
    }
    const entry: RegisteredEventType = {
      type,
      registeredAt: new Date().toISOString(),
      ...(options?.description !== undefined
        ? { description: options.description }
        : {}),
      ...(options?.stickyDefault !== undefined
        ? { stickyDefault: options.stickyDefault }
        : {}),
    };
    this.types.set(type, entry);
  }

  unregister(type: string): boolean {
    return this.types.delete(type);
  }

  exists(type: string): boolean {
    return this.types.has(type);
  }

  get(type: string): RegisteredEventType | undefined {
    return this.types.get(type);
  }

  list(): readonly RegisteredEventType[] {
    return Object.freeze([...this.types.values()]);
  }

  /** Allow unknown types (open bus) while still tracking known ones. */
  ensureKnown(type: string | StandardEventType): void {
    if (!this.types.has(type)) {
      this.register(type, { description: "Auto-registered event type" });
    }
  }

  /** Sticky map: last sticky event per type */
  private readonly sticky = new Map<string, ADOSEvent>();

  setSticky(event: ADOSEvent): void {
    this.sticky.set(event.type, event);
  }

  getSticky(type: string): ADOSEvent | undefined {
    return this.sticky.get(type);
  }

  clearSticky(type?: string): void {
    if (type) this.sticky.delete(type);
    else this.sticky.clear();
  }

  clear(): void {
    this.types.clear();
    this.sticky.clear();
  }
}
