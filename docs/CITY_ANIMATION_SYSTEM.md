# City Animation System

**Sprint:** CG-2
**Code:** `src/web/src/enterprise-city/graphics/animationController.ts`, `graphics/visualEffects.ts`
**Specification this implements against:** `ENTERPRISE_CITY_ANIMATIONS.md` (documentation-only,
Sprint-11-era) — this document describes the *engine*; `ENTERPRISE_CITY_ANIMATIONS.md` remains the
governing rule set for which triggers get which treatment.

## 1. Animation Controller — `animateValue`

A small, generic `requestAnimationFrame` tween manager. Every animated thing in the Graphics Engine —
camera transitions, and (once wired) building/district opacity/movement/scale — drives through this
one function rather than each hand-rolling its own rAF loop.

```ts
animateValue({ durationMs?, easing?, onFrame: (t: number) => void, onComplete?: () => void }): AnimationHandle
```

- Duration defaults to the design system's real `motion.normal` token (200ms) — never an invented
  value. `animationDurations` re-exports the full named scale (`instant`/`fast`/`normal`/`slow`/
  `settle`) parsed from `design-system/tokens`, for callers that want a named preset instead of a raw
  number.
- Easing accepts any of the platform's real `motion.easing*` cubic-bezier strings; `easeIn` and
  `easeEmphasized` get dedicated quad/cubic approximations, everything else (including the default,
  `easeOut`) uses a quad-out approximation — chosen because implementing a full cubic-bezier solver is
  more machinery than a City camera pan needs, and the approximation matches the same "fast start,
  gentle settle" character the real easing curve targets.
- Returns an `AnimationHandle { id, cancel() }` so an in-flight animation interrupted by a new
  pan/zoom/focus input can stop cleanly instead of fighting the next one.
- **Clock note:** `elapsed` is computed by re-reading `performance.now()` (or `Date.now()` as
  fallback) on every tick, rather than trusting the timestamp `requestAnimationFrame` passes into its
  callback. During implementation, jsdom's rAF timestamp argument was observed to use a different
  epoch than `performance.now()` in the same environment, which silently broke elapsed-time math (see
  `SPRINT_CG_2_RESULT.md` §4 for how this was caught). Reading the clock directly is correct in every
  environment, not just jsdom's.
- In a non-browser environment with no `requestAnimationFrame` at all, resolves instantly (`onFrame(1)`
  → `onComplete()`) rather than silently doing nothing.

## 2. Reduced motion

The Animation Controller itself is duration/easing-agnostic — reduced motion is handled one level up,
by each caller (`cameraEngine.ts`'s `animateViewport`, `visualEffects.ts`'s `resolveEffect`), which
collapse to a single instant frame/zero duration rather than skipping the visual end-state. This
matches `ENTERPRISE_DESIGN_SYSTEM.md` §5.5 / `ENTERPRISE_CITY_ANIMATIONS.md` §5: durations collapse,
but the correct final state always still applies.

## 3. Visual Effects — `resolveEffect`

Resolves an `EffectKind` (`hover | selection | pulse | highlight | glow | fade |
building_activation | district_activation`) to a `ResolvedEffect { className, durationMs, continuous }`
— pure data, no DOM writes. Every `className` is one of the design system's **real** preset strings
(`animationEngine.presets` — `eds-anim-*` / `edm-*`); this module mints zero new animation class names.

| Effect | Preset used | Continuous? |
|---|---|---|
| `hover` | `eds-anim-micro` | no |
| `selection` | `eds-anim-scale` | no |
| `pulse` | `edm-ai-live` | **yes** — the platform's own sanctioned "AI is active" loop |
| `highlight` | `edm-card-enter` | no |
| `glow` | `edm-kpi` | no |
| `fade` | `eds-anim-fade` | no |
| `building_activation` | `edm-card-refresh` | no |
| `district_activation` | `eds-anim-expand` | no |

`pulse` is the one continuous effect in the table, and it is continuous *only* because `edm-ai-live`
is already on the design system's `rules.maxContinuousLoops` allowlist
(`["edm-ai-live", "edm-bg-update", "edm-stream-bar", "ec-ai-dot"]`). `resolveEffect` enforces this as
a real check, not a comment: any continuous effect whose class is **not** on that allowlist is
automatically downgraded to a one-shot fade rather than silently allowed through — the one place a
City-specific effect request is checked against the platform's own animation governance rule
(`animationEngine.rules`, `design-system/animation/index.ts`).

`isForbiddenAnimationClass(className)` is a defense-in-depth check against the design system's
explicit forbidden list (`bounce`, `spin-on-page`, `parallax-scroll`, `autoplay-carousel`) — useful for
a future dev-tools lint pass over any dynamically-constructed class name.

## 4. What this system deliberately does not do

- No business logic — an effect kind says nothing about *why* a building should glow; a consumer
  decides that from real state (e.g. `cityVisualLanguage.ts`'s existing visual states) and only asks
  this module to resolve the *how*.
- No new continuous-loop exceptions beyond what the design system already allows — `pulse` reuses the
  existing one; nothing here proposes a new ambient/idle animation.
- No animation timing scale distinct from the rest of the platform — every duration traces back to
  `motion` in `design-system/tokens`.

## 5. Test coverage

`graphics.test.ts` → `describe("animation controller")` and `describe("visual effects")`: frames
progress from >0 toward exactly 1 and complete, a cancelled handle stops producing frames, every
effect kind resolves to a non-empty class with a non-negative duration, `reducedMotion` collapses
duration to 0, `pulse` is confirmed continuous specifically because its class is allowlisted, and
`isForbiddenAnimationClass` flags a `bounce`-containing name while passing a real preset through.
