import type { LifecycleState } from "./types.js";

export type LifecycleTransitionListener = (
  from: LifecycleState,
  to: LifecycleState,
) => void;

/**
 * Finite-state lifecycle controller for kernel objects and services.
 */
export interface ILifecycle {
  readonly state: LifecycleState;
  canTransition(to: LifecycleState): boolean;
  transition(to: LifecycleState): void;
  assertState(...allowed: LifecycleState[]): void;
  onTransition(listener: LifecycleTransitionListener): () => void;
  reset(): void;
}
