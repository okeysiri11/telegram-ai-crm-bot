import type {
  ADOSEvent,
  EventDeliveryMode,
  EventInput,
  EventMetadata,
  EventPriority,
} from "./types.js";

let sequenceCounter = 0;

/** Generate monotonic sequence numbers (process-local). */
export function nextSequence(): number {
  sequenceCounter += 1;
  return sequenceCounter;
}

/** Reset sequence — tests only. */
export function resetSequenceForTests(): void {
  sequenceCounter = 0;
}

function createId(): string {
  return `evt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Immutable event factory / value object.
 */
export class Event<TPayload = unknown> implements ADOSEvent<TPayload> {
  readonly id: string;
  readonly type: string;
  readonly payload: TPayload;
  readonly priority: EventPriority;
  readonly mode: EventDeliveryMode;
  readonly delayMs: number;
  readonly sticky: boolean;
  readonly metadata: EventMetadata;
  readonly timestamp: string;
  readonly sequence: number;

  private constructor(init: ADOSEvent<TPayload>) {
    this.id = init.id;
    this.type = init.type;
    this.payload = init.payload;
    this.priority = init.priority;
    this.mode = init.mode;
    this.delayMs = init.delayMs;
    this.sticky = init.sticky;
    this.metadata = init.metadata;
    this.timestamp = init.timestamp;
    this.sequence = init.sequence;
  }

  static create<TPayload = unknown>(
    input: EventInput<TPayload>,
  ): Event<TPayload> {
    if (!input.type || input.type.trim() === "") {
      throw new Error("Event type is required");
    }
    const mode: EventDeliveryMode = input.mode ?? "async";
    if (mode === "delayed" && (input.delayMs === undefined || input.delayMs < 0)) {
      throw new Error("delayed events require delayMs >= 0");
    }

    return new Event<TPayload>({
      id: input.id ?? createId(),
      type: input.type,
      payload: (input.payload ?? null) as TPayload,
      priority: input.priority ?? 0,
      mode,
      delayMs: mode === "delayed" ? (input.delayMs ?? 0) : 0,
      sticky: input.sticky === true,
      metadata: Object.freeze({ ...(input.metadata ?? {}) }),
      timestamp: new Date().toISOString(),
      sequence: nextSequence(),
    });
  }

  static fromExisting<TPayload = unknown>(
    event: ADOSEvent<TPayload>,
  ): Event<TPayload> {
    return new Event(event);
  }

  toJSON(): ADOSEvent<TPayload> {
    return {
      id: this.id,
      type: this.type,
      payload: this.payload,
      priority: this.priority,
      mode: this.mode,
      delayMs: this.delayMs,
      sticky: this.sticky,
      metadata: this.metadata,
      timestamp: this.timestamp,
      sequence: this.sequence,
    };
  }
}
