/**
 * Enterprise City Graphics Engine — Visual Effects.
 * Sprint CG-2. Resolves an `EffectKind` to a ready-to-apply CSS class + duration. Pure presentation —
 * no business logic, no state, no store. Reuses the real Motion Design Language presets/rules from
 * `design-system/animation` (`animationEngine`) rather than inventing a second animation vocabulary;
 * the platform's forbidden-animation list (`bounce`, `spin-on-page`, `parallax-scroll`,
 * `autoplay-carousel`) is enforced here too, since City buildings are exactly the kind of surface
 * that "activation" effects could otherwise be tempted to abuse.
 */

import { animationEngine } from "../../../design-system/animation";
import type { EffectKind, ResolvedEffect } from "./types";

const { durations, presets, rules } = animationEngine;

/**
 * Effect → design-system preset class + duration. Every className below is one of the platform's
 * real preset strings (`eds-anim-*` / `edm-*`) — City never mints its own animation class names.
 */
const EFFECT_TABLE: Record<EffectKind, Omit<ResolvedEffect, "kind">> = {
  hover: { className: presets.micro, durationMs: Number.parseInt(durations.fast, 10), continuous: false },
  selection: { className: presets.scale, durationMs: Number.parseInt(durations.normal, 10), continuous: false },
  pulse: { className: "edm-ai-live", durationMs: Number.parseInt(durations.slow, 10), continuous: true },
  highlight: { className: presets.cardEnter, durationMs: Number.parseInt(durations.normal, 10), continuous: false },
  glow: { className: presets.kpiUpdate, durationMs: Number.parseInt(durations.slow, 10), continuous: false },
  fade: { className: presets.fade, durationMs: Number.parseInt(durations.normal, 10), continuous: false },
  building_activation: { className: presets.cardRefresh, durationMs: Number.parseInt(durations.settle, 10), continuous: false },
  district_activation: { className: presets.expand, durationMs: Number.parseInt(durations.settle, 10), continuous: false },
};

/**
 * Resolve an effect, honoring the platform's continuous-loop allowlist and reduced-motion contract.
 * Any continuous effect not on `rules.maxContinuousLoops` is downgraded to a one-shot fade rather than
 * silently allowed — this is the one place City-specific effect requests are checked against that rule.
 */
export function resolveEffect(kind: EffectKind, reducedMotion = false): ResolvedEffect {
  const entry = EFFECT_TABLE[kind];
  if (reducedMotion) {
    return { kind, className: entry.className, durationMs: 0, continuous: false };
  }
  if (entry.continuous && !(rules.maxContinuousLoops as readonly string[]).includes(entry.className)) {
    return { kind, className: presets.fade, durationMs: entry.durationMs, continuous: false };
  }
  return { kind, ...entry };
}

/** All effect kinds — useful for a Debug layer legend or an effect-picker in dev tools. */
export function allEffectKinds(): EffectKind[] {
  return Object.keys(EFFECT_TABLE) as EffectKind[];
}

/** True if `className` is one the design system explicitly forbids (defense in depth). */
export function isForbiddenAnimationClass(className: string): boolean {
  return (rules.forbidden as readonly string[]).some((f) => className.includes(f));
}
