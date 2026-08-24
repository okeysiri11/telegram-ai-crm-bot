/**
 * Odessa asset lifecycle, boot phases, heavy-class, and activation budget.
 * Load (fetch/parse) is separate from scene activation.
 */

import type { AssetLifecycle, BootState, HeavyClass } from "./types";

export type { AssetLifecycle, BootState, HeavyClass };

const TRANSITIONS: Record<AssetLifecycle, readonly AssetLifecycle[]> = {
  queued: ["fetching", "failed"],
  fetching: ["waiting_parse", "parsing", "failed"],
  waiting_parse: ["parsing", "failed"],
  parsing: ["parsed", "failed"],
  parsed: ["preparing", "failed"],
  preparing: ["ready", "failed"],
  ready: ["active", "failed"],
  active: ["hidden", "failed"],
  hidden: ["active", "failed"],
  failed: [],
};

export function canTransitionLifecycle(from: AssetLifecycle, to: AssetLifecycle): boolean {
  if (from === to) return true;
  return TRANSITIONS[from].includes(to);
}

export function transitionLifecycle(from: AssetLifecycle, to: AssetLifecycle): AssetLifecycle {
  if (!canTransitionLifecycle(from, to)) {
    throw new Error(`invalid_lifecycle:${from}->${to}`);
  }
  return to;
}

export const LIGHT_TRI_MAX = 100_000;
export const MEDIUM_TRI_MAX = 500_000;
export const HEAVY_TRI_MAX = 1_500_000;

export function classifyHeavyAsset(input: {
  triangles?: number;
  sizeMb?: number;
  layerId?: string;
}): HeavyClass {
  let tris = input.triangles ?? 0;
  if (tris <= 0 && input.sizeMb) {
    tris = input.sizeMb * 18_000;
  }
  if (input.layerId === "heavy" && tris < MEDIUM_TRI_MAX) {
    tris = Math.max(tris, MEDIUM_TRI_MAX);
  }
  if (tris > HEAVY_TRI_MAX) return "EXTREME";
  if (tris > MEDIUM_TRI_MAX) return "HEAVY";
  if (tris > LIGHT_TRI_MAX) return "MEDIUM";
  return "LIGHT";
}

export const ACTIVATION_BUDGET_IDLE_MS = 5.5;
export const ACTIVATION_BUDGET_IDLE_HEALTHY_MS = 6.5;
export const ACTIVATION_BUDGET_SETTLING_MS = 2;
export const ACTIVATION_BUDGET_INTERACTING_MS = 0;
export const ACTIVATION_LOW_FPS = 28;
export const ACTIVATION_HEALTHY_FPS = 50;

export function activationBudgetMs(mode: "IDLE" | "INTERACTING" | "SETTLING", fps: number): number {
  if (mode === "INTERACTING") return ACTIVATION_BUDGET_INTERACTING_MS;
  if (mode === "SETTLING") return ACTIVATION_BUDGET_SETTLING_MS;
  if (fps > 0 && fps < ACTIVATION_LOW_FPS) return 3;
  if (fps >= ACTIVATION_HEALTHY_FPS) return ACTIVATION_BUDGET_IDLE_HEALTHY_MS;
  return ACTIVATION_BUDGET_IDLE_MS;
}

export function estimateActivationCostMs(heavyClass: HeavyClass): number {
  switch (heavyClass) {
    case "LIGHT":
      return 2;
    case "MEDIUM":
      return 5;
    case "HEAVY":
      return 8;
    case "EXTREME":
      return 14;
  }
}

export function canActivateThisFrame(spentMs: number, estimateMs: number, budgetMs: number, heavyClass: HeavyClass): boolean {
  if (budgetMs <= 0) return false;
  if (spentMs <= 0) return true;
  if (heavyClass === "HEAVY" || heavyClass === "EXTREME") return false;
  return spentMs + estimateMs <= budgetMs;
}

export type ActivationPriorityInput = {
  distanceM: number;
  inFrustum: boolean;
  nearTarget: boolean;
  manifestPriority: boolean;
  heavyClass: HeavyClass;
};

/** Lower score activates first. */
export function scoreActivationPriority(input: ActivationPriorityInput): number {
  let score = input.distanceM;
  if (input.manifestPriority) score -= 5000;
  if (input.nearTarget) score -= 2500;
  if (input.inFrustum) score -= 2000;
  if (input.heavyClass === "HEAVY") score += 600;
  if (input.heavyClass === "EXTREME") score += 1200;
  return score;
}

export function resolveBootState(input: { total: number; failed: number; active: number }): BootState {
  const remaining = Math.max(0, input.total - input.failed);
  if (input.active <= 0) return "BOOTSTRAP";
  if (remaining > 0 && input.active >= remaining) return "READY";
  if (input.active < 3) return "INTERACTIVE";
  return "FILLING";
}
