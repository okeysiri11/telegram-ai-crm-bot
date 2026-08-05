# City Camera Engine

**Sprint:** CG-2 (§1–§5, real, shipped), extended by CG-3 (§5.1) and specified further by CG-4 (§6,
research/spec only — no code)
**Code:** `src/web/src/enterprise-city/graphics/cameraEngine.ts`
**Extends (does not replace):** `src/web/src/enterprise-city/cityEngine.ts` (Sprint 27.8)

> **CG-3 reality update:** `useCityGraphicsRuntime.ts` is now the real caller of every function in
> §1 — it wraps them with a `liveViewportRef` (so a second animation started mid-flight doesn't
> restart from a stale position), direct-DOM transform writes (no per-frame React re-render), and an
> fps-limit throttle. See `SPRINT_CG_3_RESULT.md` for the integration. §1–§5 below describe
> `cameraEngine.ts` itself, which CG-3 did not modify.

## 0. Relationship to `cityEngine.ts`

`cityEngine.ts`'s own header calls itself a "presentation camera controller," and its own non-goals
list includes "WebGL camera" — it owns `CityViewport`, clamping, `panToBuilding`, pan/zoom deltas, and
session persistence, but every state change it produces is instantaneous (no interpolation). CG-2's
Camera Engine adds exactly the one thing `cityEngine.ts` intentionally does not do: **smoothing a
transition between two viewports over time**. It imports `clampViewport`, `DEFAULT_VIEWPORT`, and
`panToBuilding` directly rather than re-implementing any of them.

Reusable by every City screen — nothing in `cameraEngine.ts` depends on `EnterpriseCityPage.tsx` or
any specific consumer.

## 1. API

```ts
animateViewport(from: CityViewport, to: CityViewport, options: CameraAnimationOptions): AnimationHandle
focusBuilding(current: CityViewport, building: CityBuilding, options): AnimationHandle
focusDistrict(current: CityViewport, district: CityDistrictMeta, options): AnimationHandle
resetCamera(current: CityViewport, options): AnimationHandle
cameraBounds(): { zoomMin: number; zoomMax: number; panLimit: number }
```

`CameraAnimationOptions`:

```ts
{ durationMs?: number; reducedMotion?: boolean; onFrame: (v: CityViewport) => void; onComplete?: (v: CityViewport) => void }
```

- **`animateViewport`** — the base primitive. Interpolates `x`/`y`/`zoom` linearly, clamping every
  intermediate frame through the real `clampViewport` (so an in-flight animation can never produce an
  out-of-bounds viewport, even mid-tween). Default duration is 320ms — the platform's `slow` motion
  token, matching `ENTERPRISE_CITY_ANIMATIONS.md` §2's "Viewport pan/zoom" entry.
- **`focusBuilding`** — thin wrapper: computes the target with the real `panToBuilding(building,
  current)`, then animates to it. Note the real `panToBuilding` keeps the *current* zoom unless no
  current viewport is given (`current?.zoom ?? 1.15`) — this is `cityEngine.ts`'s existing behavior,
  unchanged.
- **`focusDistrict`** — centers the camera on a district's real centroid (`CityDistrictMeta.x/y`) at a
  fixed 0.85 zoom, wide enough to frame a whole district rather than a single building.
- **`resetCamera`** — animates back to `DEFAULT_VIEWPORT`, the camera's one "home" position.
- **`cameraBounds`** — exposes `zoomMin`/`zoomMax`/`panLimit` as data (for a zoom slider, a minimap,
  or a debug overlay) by **probing** the real `clampViewport` with extreme inputs
  (`clampViewport({x:0,y:0,zoom:999})`, etc.) rather than re-declaring `cityEngine.ts`'s private
  `ZOOM_MIN`/`ZOOM_MAX`/`PAN_LIMIT` constants a second time. If those constants ever change, this
  function's return value changes with them automatically — there is exactly one source of truth.

## 2. Reduced motion

Every animated function honors `options.reducedMotion` identically: instead of scheduling frames, it
calls `onFrame`/`onComplete` once, synchronously, with the final clamped target. This is the same
contract every other animated surface in the platform honors
(`ENTERPRISE_DESIGN_SYSTEM.md` §5.5, restated for the City in `ENTERPRISE_CITY_ANIMATIONS.md` §5) —
applied here, not reinvented.

## 3. How animation is actually driven

`animateViewport` delegates the 0→1 tween to `animateValue` (`animationController.ts` —
see `CITY_ANIMATION_SYSTEM.md`), then lerps `from`→`to` per-axis using the eased `t` value and
re-clamps. The Camera Engine itself contains no `requestAnimationFrame` call and no easing math
duplicate of the animation controller's.

## 4. Non-goals (unchanged from `cityEngine.ts`, restated here for clarity)

- No physics/pathfinding.
- No server-side camera sync.
- No WebGL/canvas camera — output is still plain interpolated numbers a DOM/CSS transform consumes,
  identical in kind to what `cityEngine.ts` already produces.
- No new persistence — this module does not read/write `ews_city_viewport_v1` itself; a consuming
  screen is expected to call the real `writeViewport()` once an animation completes, exactly as it
  does today for instantaneous camera changes.

## 5. Test coverage

`graphics.test.ts` → `describe("camera engine")`: bounds match the real 0.65/1.75/35 limits,
reduced-motion collapses to exactly one frame, `focusBuilding` reaches the exact value the real
`panToBuilding` would produce, `focusDistrict` lands on a clamped viewport, `resetCamera` reaches
`DEFAULT_VIEWPORT` exactly.

## 6. Runtime Specification (CG-4 — SPEC, no code)

Covers the brief's remaining camera behaviors not yet built: **follow**, **focus event**,
**multi-monitor support**, and **future 3D compatibility**. Zoom, focus building, focus district, and
smooth transitions are already real (§1–§5) — not repeated here.

### 6.1 Follow (SPEC)

"Follow" means the camera keeps a moving target framed automatically — relevant once
`CITY_SIMULATION.md` §2's agent-movement visualization exists (an agent icon traveling between
buildings). Proposed API, additive to §1, no change to existing signatures:

```ts
// SPEC — proposed addition to cameraEngine.ts
followTarget(
  getTargetViewport: () => CityViewport,   // called once per render tick, not owned by camera engine
  options: CameraAnimationOptions & { stopWhen?: () => boolean },
): AnimationHandle
```

Design constraint: `followTarget` must **not** introduce its own polling loop — it is proposed as a
thin wrapper that re-issues `animateViewport` toward `getTargetViewport()`'s latest value each time the
render tick already runs (`CITY_RUNTIME.md` §4), reusing the exact cancel-and-retarget behavior CG-3's
`runCameraTween` already implements for rapid wheel input. A `stopWhen` guard (e.g. "target reached its
destination building") ends follow mode without the caller needing a separate teardown path.

Follow must be interruptible by any user input instantly (drag, wheel, explicit focus click) — the
existing `cancelActiveAnimation` (CG-3) already provides this; follow mode is proposed to register
itself through the same `activeHandleRef`, not a parallel handle.

### 6.2 Focus Event (SPEC)

When a Live Event (`CITY_EVENTS.md`) is significant enough to warrant a camera reaction (e.g. a
Critical alert on a building currently off-screen), the camera **may** auto-focus it — but this is the
single most disruptive thing the camera can do (it moves the user's view without a click), so it is
proposed under a strict guard, not an unconditional reaction:

1. Only `severity: "critical"` events (§`CityEventPayload` in `CITY_EVENTS.md` §3) are eligible.
2. Never fires if the user has interacted with the camera (drag/wheel/click-focus) in the last 5s —
   "don't steal the wheel." Source: the same input-activity signal `CITY_RUNTIME.md` §3's Idle-mode
   timer already needs, reused rather than duplicated.
3. Never fires more than once per N seconds platform-wide (proposed 20s), to prevent an event storm
   from turning the City into a strobe.
4. Always uses `focusBuildingAnimated`/`focusDistrictAnimated` (§1, real) — a focus-event reaction is
   not a new camera primitive, just a new *caller* of the existing ones, gated by the rules above.

### 6.3 Multi-monitor support (SPEC — vision, not scheduled)

The camera model is entirely percentage-space (`CityViewport { x, y, zoom }` relative to the
`.ec-map-shell` container, per `cityEngine.ts`), which already makes it viewport-size-agnostic — the
same `CityViewport` value produces a correct frame on any container size, including a browser window
spanning multiple monitors or a City instance rendered independently per monitor. **No change is
required in the camera model itself** for basic multi-monitor display. What is genuinely unbuilt: a
way for two independent City instances (e.g. one per monitor, or a "presentation mode" secondary
window) to optionally *share* camera state — proposed as a future `BroadcastChannel`-based sync
(browser-native, no new server infra) between instances that opt in, explicitly out of scope for any
near-term sprint per the brief's own "not scheduled" framing of 3D/multi-monitor items.

### 6.4 Future 3D compatibility (SPEC — vision, explicitly deferred)

CG-2's own non-goals (§4) already state "no WebGL/canvas camera" — this section documents *why the
current design doesn't block a future 3D mode*, not a plan to build one now:

- `CityViewport { x, y, zoom }` maps cleanly onto a 3D camera's `(position.x, position.y, distance)` —
  a future 3D renderer could consume the exact same `CityViewport` values `cameraEngine.ts` already
  produces, translating them at the render layer rather than requiring a second camera model.
- `focusBuilding`/`focusDistrict`/`resetCamera`/`followTarget` (§6.1) are all *target resolution*
  functions — they compute a `CityViewport`, they do not know or care how that viewport gets painted.
  A 3D render pipeline would consume the same target-resolution functions unchanged.
- What a 3D mode would add, not replace: a `z`/pitch/orbit component the current 2D `CityViewport`
  has no field for. Proposed (not scheduled): a strictly optional `CityViewport3D extends CityViewport`
  with `pitch?: number; orbit?: number`, so a 2D consumer never needs to change and a 3D consumer opts
  in additively — the same "extend, don't replace" pattern this whole engine has followed since CG-2.

This section exists so a future 3D sprint does not need to redesign the camera's target-resolution
API — it can extend `CityViewport` and reuse `cameraEngine.ts`'s functions as-is.
