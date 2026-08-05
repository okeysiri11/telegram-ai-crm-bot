import type { KernelEventMap } from "./types.js";

export type EventHandler<T> = (payload: T) => void | Promise<void>;

/**
 * Minimal kernel event bus. Business modules may subscribe later via plugins —
 * the kernel only publishes infrastructure events (e.g. BootCompleted).
 */
export interface IEventBus {
  publish<K extends keyof KernelEventMap>(
    event: K,
    payload: KernelEventMap[K],
  ): Promise<void>;
  subscribe<K extends keyof KernelEventMap>(
    event: K,
    handler: EventHandler<KernelEventMap[K]>,
  ): () => void;
  clear(): void;
}
