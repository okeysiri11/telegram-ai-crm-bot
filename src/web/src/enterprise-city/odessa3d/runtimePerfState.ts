/**
 * Odessa 3D camera interaction runtime: IDLE → INTERACTING → SETTLING.
 * Streaming and optional quality dips key off this; does not move city geometry.
 */

export type RuntimePerfMode = "IDLE" | "INTERACTING" | "SETTLING";

/** Restore streaming after camera rest. Quality DPR restore uses QUALITY_IDLE_BOOST_MS. */
export const SETTLE_MS = 650;

export class InteractionRuntimeState {
  private mode: RuntimePerfMode = "IDLE";
  private pointerDown = false;
  private lastMotionAt = 0;

  getMode(): RuntimePerfMode {
    return this.mode;
  }

  start(now: number) {
    this.pointerDown = true;
    this.mode = "INTERACTING";
    this.lastMotionAt = now;
  }

  end(now: number) {
    this.pointerDown = false;
    this.lastMotionAt = now;
    this.mode = "SETTLING";
  }

  tick(now: number, cameraMoved: boolean): RuntimePerfMode {
    if (cameraMoved) this.lastMotionAt = now;
    if (this.pointerDown) {
      this.mode = "INTERACTING";
      return this.mode;
    }
    if (this.mode === "INTERACTING") {
      this.mode = "SETTLING";
    }
    if (this.mode === "SETTLING" && now - this.lastMotionAt >= SETTLE_MS) {
      this.mode = "IDLE";
    }
    return this.mode;
  }

  shouldPauseStreaming(): boolean {
    return this.mode === "INTERACTING";
  }

  shouldDeferVisibilityPass(): boolean {
    return this.mode === "INTERACTING";
  }

  shouldPauseHeavyUnload(): boolean {
    return this.mode !== "IDLE";
  }

  /**
   * Immediate DPR dip is disabled (STEP 26): resolution only changes via
   * AdaptivePixelRatioController hysteresis, never on the first orbit frame.
   */
  shouldDipPixelRatio(): boolean {
    return false;
  }
}

export function streamConcurrencyForMode(base: number, mode: RuntimePerfMode, fpsGuardCap: number): number {
  const cap = Math.max(1, Math.min(base, fpsGuardCap));
  if (mode === "INTERACTING") return cap;
  if (mode === "SETTLING") return Math.min(1, cap);
  return cap;
}

/** Kept for tests; STEP 26 no longer dips DPR on interaction. */
export function interactionPixelRatio(baseRatio: number, dip: boolean): number {
  if (!dip) return baseRatio;
  return baseRatio;
}
