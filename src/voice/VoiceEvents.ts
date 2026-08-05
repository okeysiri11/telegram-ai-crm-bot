import type { VoiceEvent, VoiceEventType } from "./types.js";

export type VoiceEventListener = (event: VoiceEvent) => void;

/**
 * Voice event emitter — feeds Runtime WS broadcaster.
 */
export class VoiceEvents {
  private readonly listeners = new Set<VoiceEventListener>();

  on(listener: VoiceEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit(type: VoiceEventType, payload: unknown): VoiceEvent {
    const event: VoiceEvent = {
      type,
      at: new Date().toISOString(),
      payload,
    };
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch {
        /* ignore listener errors */
      }
    }
    return event;
  }
}

export function createVoiceEvents(): VoiceEvents {
  return new VoiceEvents();
}
