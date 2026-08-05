import type { ILifecycle, LifecycleTransitionListener } from "./interfaces/ILifecycle.js";
import type { LifecycleState } from "./interfaces/types.js";

const ALLOWED: Readonly<Record<LifecycleState, readonly LifecycleState[]>> = {
  Created: ["Initialized", "Disposed"],
  Initialized: ["Started", "Stopped", "Disposed"],
  Started: ["Paused", "Stopped"],
  Paused: ["Started", "Stopped"],
  Stopped: ["Initialized", "Started", "Disposed"],
  Disposed: [],
};

/**
 * Finite-state lifecycle with validated transitions.
 */
export class Lifecycle implements ILifecycle {
  private _state: LifecycleState;
  private readonly listeners = new Set<LifecycleTransitionListener>();

  constructor(initial: LifecycleState = "Created") {
    this._state = initial;
  }

  get state(): LifecycleState {
    return this._state;
  }

  canTransition(to: LifecycleState): boolean {
    if (to === this._state) {
      return true;
    }
    return ALLOWED[this._state].includes(to);
  }

  transition(to: LifecycleState): void {
    if (to === this._state) {
      return;
    }
    if (!this.canTransition(to)) {
      throw new Error(
        `Invalid lifecycle transition: ${this._state} → ${to}`,
      );
    }
    const from = this._state;
    this._state = to;
    for (const listener of this.listeners) {
      listener(from, to);
    }
  }

  assertState(...allowed: LifecycleState[]): void {
    if (!allowed.includes(this._state)) {
      throw new Error(
        `Expected lifecycle state in [${allowed.join(", ")}], got ${this._state}`,
      );
    }
  }

  onTransition(listener: LifecycleTransitionListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  reset(): void {
    this._state = "Created";
  }
}
