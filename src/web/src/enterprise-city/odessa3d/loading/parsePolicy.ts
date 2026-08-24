/**
 * Parse / fetch policy for heavy Odessa GLBs.
 * Reuses STEP 22 heavy-class and STEP 21 FPS guards — no duplicate triangle tables.
 */

import {
  ACTIVATION_LOW_FPS,
  classifyHeavyAsset,
  type BootState,
  type HeavyClass,
} from "../assetLifecycle";
import type { RuntimePerfMode } from "../runtimePerfState";

export type ParseBand = "NEAR" | "MID" | "TARGET" | "FAR" | "EDGE" | "OUTSIDE";

export const PARSE_CONCURRENCY = 1;
export const MAX_HEAVY_PARSES_PER_TURN = 1;

export const WAITING_PARSE_COUNT_LIMIT = 3;
export const WAITING_PARSE_MB_LIMIT = 48;
export const WAITING_ACTIVATION_COUNT_LIMIT = 8;
export const WAITING_ACTIVATION_MB_LIMIT = 80;

export const FETCH_RETRY_MAX = 2;
export const FETCH_RETRY_BASE_MS = 400;

export const LIGHT_INTERACT_MAX_LAST_PARSE_MS = 50;
export const LIGHT_INTERACT_MIN_FPS = ACTIVATION_LOW_FPS;

export const PARSE_STARVE_MS = 8000;

const BAND_RANK: Record<ParseBand, number> = {
  NEAR: 0,
  MID: 1,
  TARGET: 2,
  FAR: 3,
  EDGE: 4,
  OUTSIDE: 5,
};

const RANK_TO_BAND: ParseBand[] = ["NEAR", "MID", "TARGET", "FAR", "EDGE", "OUTSIDE"];

export { classifyHeavyAsset };

export function parseBandRank(band: ParseBand): number {
  return BAND_RANK[band];
}

export function classifyParseBand(input: {
  distanceM: number;
  inFrustum: boolean;
  nearTarget: boolean;
  nearM: number;
  midM: number;
  farM: number;
}): ParseBand {
  if (input.distanceM <= input.nearM) return "NEAR";
  if (input.distanceM <= input.midM) return input.inFrustum ? "MID" : "EDGE";
  if (input.nearTarget) return "TARGET";
  if (input.inFrustum && input.distanceM <= input.farM) return "FAR";
  if (input.distanceM <= input.farM) return "EDGE";
  return "OUTSIDE";
}

/** Bounded promotion so an OUTSIDE LIGHT cannot starve forever behind a stream of slightly nearer files. */
export function applyParseStarvation(band: ParseBand, waitMs: number): ParseBand {
  if (waitMs < PARSE_STARVE_MS) return band;
  const shift = Math.min(2, Math.floor(waitMs / PARSE_STARVE_MS));
  const next = Math.max(0, BAND_RANK[band] - shift);
  return RANK_TO_BAND[next] ?? band;
}

export function isHeavyParseClass(heavyClass: HeavyClass): boolean {
  return heavyClass === "HEAVY" || heavyClass === "EXTREME";
}

export type ParseStartInput = {
  heavyClass: HeavyClass;
  mode: RuntimePerfMode;
  fps: number;
  lastParseMs: number;
  bootState: BootState;
  nearTarget: boolean;
  seaProtected: boolean;
  screenImportant?: boolean;
  parseBand: ParseBand;
  prefetch?: boolean;
  higherPriorityWaiting: boolean;
  currentlyParsing: boolean;
};

/**
 * Whether a parse may *start*. A parse that already entered GLTFLoader.parse
 * cannot be preempted — JavaScript has no cancel for that stack.
 */
export function canStartParse(input: ParseStartInput): boolean {
  if (input.currentlyParsing) return false;
  if (input.prefetch && input.higherPriorityWaiting) return false;

  if (input.mode === "INTERACTING") {
    return canParseLightDuringInteraction(input.heavyClass, input.lastParseMs, input.fps);
  }

  if (shouldDeferExtreme(input)) return false;

  if (input.mode === "SETTLING" && isHeavyParseClass(input.heavyClass) && !isProtectedParse(input)) {
    return false;
  }

  return true;
}

export function canParseLightDuringInteraction(
  heavyClass: HeavyClass,
  lastParseMs: number,
  fps: number,
): boolean {
  if (heavyClass !== "LIGHT") return false;
  if (lastParseMs >= LIGHT_INTERACT_MAX_LAST_PARSE_MS) return false;
  if (fps > 0 && fps < LIGHT_INTERACT_MIN_FPS) return false;
  return true;
}

export function isProtectedParse(input: {
  nearTarget: boolean;
  seaProtected: boolean;
  screenImportant?: boolean;
}): boolean {
  return input.nearTarget || input.seaProtected || !!input.screenImportant;
}

export function shouldDeferExtreme(input: {
  heavyClass: HeavyClass;
  bootState: BootState;
  mode: RuntimePerfMode;
  nearTarget: boolean;
  seaProtected: boolean;
  screenImportant?: boolean;
  higherPriorityWaiting: boolean;
}): boolean {
  if (input.heavyClass !== "EXTREME") return false;
  if (isProtectedParse(input)) return false;
  if (input.mode !== "IDLE") return true;
  if (input.bootState === "BOOTSTRAP" || input.bootState === "INTERACTIVE") return true;
  if (input.higherPriorityWaiting) return true;
  return false;
}

export type BackpressureInput = {
  waitingParseCount: number;
  waitingParseMb: number;
  waitingActivationCount: number;
  waitingActivationMb: number;
};

export function isBackpressured(input: BackpressureInput): boolean {
  return (
    input.waitingParseCount >= WAITING_PARSE_COUNT_LIMIT ||
    input.waitingParseMb >= WAITING_PARSE_MB_LIMIT ||
    input.waitingActivationCount >= WAITING_ACTIVATION_COUNT_LIMIT ||
    input.waitingActivationMb >= WAITING_ACTIVATION_MB_LIMIT
  );
}

/** Critical fetches (sea / look-at / visible NEAR) may proceed even under backpressure. */
export function canStartFetch(input: {
  backpressure: boolean;
  prefetch?: boolean;
  seaProtected?: boolean;
  nearTarget?: boolean;
  parseBand?: ParseBand;
}): boolean {
  if (input.prefetch && input.backpressure) return false;
  if (!input.backpressure) return true;
  if (input.seaProtected || input.nearTarget) return true;
  if (input.parseBand === "NEAR" || input.parseBand === "MID") return true;
  return false;
}

export function isRetryableFetchError(message: string): boolean {
  if (/INVALID_GLB|GLTF_|HTML_RESPONSE|NO_MESHES|parse failure/i.test(message)) return false;
  if (/HTTP 4\d{2}/.test(message) && !/HTTP 408|HTTP 429/.test(message)) return false;
  if (/priority_cancel|aborted_priority/i.test(message)) return false;
  return true;
}

export function fetchRetryDelayMs(attempt: number): number {
  return FETCH_RETRY_BASE_MS * 3 ** Math.max(0, attempt);
}

export function isPriorityCancelSafe(input: {
  parsing: boolean;
  seaProtected: boolean;
  nearTarget: boolean;
  parseBand: ParseBand;
  inFrustum: boolean;
}): boolean {
  if (input.parsing) return false;
  if (input.seaProtected || input.nearTarget) return false;
  if (input.inFrustum && (input.parseBand === "NEAR" || input.parseBand === "MID" || input.parseBand === "FAR")) {
    return false;
  }
  return input.parseBand === "OUTSIDE" || input.parseBand === "EDGE";
}
