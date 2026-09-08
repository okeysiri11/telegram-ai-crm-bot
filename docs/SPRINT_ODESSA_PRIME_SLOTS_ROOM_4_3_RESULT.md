# Odessa Prime Casino — Phase 4.3 Slots Hall Image-First Rebuild

**Date:** 2026-09-07
Replaces the Phase 4.0–4.2 CSS/DOM cabinet illustration with an image-first composited
architecture. Routes, the demo slot engine (`slotEngine.ts`/`useSlotDemo.ts`), and the
server-authoritative Odessa Gold machine are unchanged.

## Why this sprint happened

Phase 4.2's own architectural decision recorded: *"Extend the existing React + CSS
`PhysicalSlotMachine`/`SlotsHall` path. No WebGL, no new package, no engine rewrite."*
That decision was correct for its goal at the time (stop looking like a web card catalog,
without new tooling), but two more passes of box-shadow/gradient/keyframe layering hit a
hard ceiling: CSS gradients and shadows can only *imply* light and material, they cannot
reproduce specular reflection, occlusion, or real depth. The result still read as "six
flat CSS constructions" rather than physical cabinets, which is the problem this sprint
was asked to fix. See `docs/SPRINT_ODESSA_PRIME_SLOTS_ROOM_4_2_RESULT.md` for the prior
decision and its rationale.

## Architectural decision (supersedes Phase 4.2's "no image assets" position)

**Decided:** move the cabinet body off live CSS/DOM entirely. Each cabinet is now a
single flattened image (`<img>`), positioned in a room-background image, with only the
reel screen staying as live DOM so the existing engine keeps rendering into it.
**Rejected alternatives:**
- **WebGL/Three.js hall** (`three` is already a dependency, used by
  `enterprise-city/odessa3d`) — rejected for this sprint because it needs real 3D
  models/textures we don't have, and the requirement (a static row + a hover/select
  zoom) doesn't need a free-roaming camera. Documented as the path to reach for if/when
  real 3D cabinet models become available.
- **More CSS on `PhysicalSlotMachine`** — rejected; this is exactly what Phase 4.1 and
  4.2 already tried twice, and the ceiling is the technique itself, not execution detail.
- **SVG cabinets** — rejected for the same reason as more CSS: still vector/flat, same
  ceiling on material realism.

## What shipped

- **Asset bake pipeline** (`scripts/casino-slots/cabinetTemplate.mjs`,
  `generate-cabinet-assets.mjs`): a Playwright-driven, offline, one-time render of an
  HTML/CSS cabinet template (richer than anything we'd afford to keep live — multiple
  gradient/shadow layers, gold trim, LED plate jackpot readout, gold belly nameplate,
  chrome control deck) into transparent PNGs, one per machine
  (`public/assets/casino/slots/cabinets/<id>.png`) plus one opaque hall background
  (`public/assets/casino/slots/hall-bg.png`). The script also measures the baked
  screen bezel's exact rect via `getBoundingClientRect()` and each variant's canvas
  aspect ratio, and writes both into the generated
  `src/casino/games/slots/cabinetGeometry.generated.ts`.
- **`PhysicalSlotMachine.tsx`** rewritten: renders the baked `<img>`, a floor reflection
  (the same image, flipped and masked), two lightweight idle-glow overlays (LED pulse,
  jackpot shimmer — both `mix-blend-mode:screen`, not a redrawn cabinet), and the
  **live screen overlay** (unchanged `SlotReels`-style DOM: reel grid, theme art, glass
  glare, glass sweep) absolutely positioned at the baked-and-measured screen rect. The
  cabinet's own accessible name comes from `aria-label` on the link (title + jackpot),
  since the visual text is now inside the image (an empty-`alt` decorative image);
  visually-hidden but DOM-present nodes keep the existing test/automation contract
  (`slot-topper-*`, `slot-controls-*`).
- **`slotsHall.css`** cut from 699 to ~380 lines: all cabinet-shell CSS (gradients,
  box-shadow stacks, per-variant border-radius, LED rail/side elements, belly/deck/base
  styling) is gone. What remains only positions the image, the screen overlay, and a
  handful of idle-animation overlays, plus the pre-existing viewport-lock and subnav
  rules (untouched).
- **`.op-slots-env`**: the six live decorative "room" layers (ceiling/chandelier/
  columns/haze/depth/floor) are replaced by the single baked hall background image.
- **Layout fix (the actual hard part):** cabinets are sized via CSS `aspect-ratio`
  (inline, per `cabinetVariant`) so the rendered `<img>` box always matches the baked
  PNG's native ratio — curved/square/slim machines are genuinely different widths now,
  not a shared box with distorted content. This required moving `.op-slots-row` from
  flexbox to CSS Grid with one equal-width column per machine (`--slot-count` set
  inline from the filtered catalog length): flexbox's shrink algorithm does not combine
  predictably with `aspect-ratio` across three different ratios sharing one row, while a
  grid column's width is deterministic before the aspect-ratio sizing runs. Every rule
  and media-query override was audited to never pin both width *and* height on
  `.op-phys-cab` at once — only one axis is ever definite, the other is `auto` (+
  `max-*` as a soft cap) — which is what actually prevents squish.
- Tests: `slotsHall.test.tsx` keeps all 10 existing assertions passing unmodified
  (same test ids, same routes, same CSS-substring checks) and adds three new cases:
  every cabinet has its baked `<img>` asset + a percentage-positioned screen overlay;
  clicking a cabinet flags `is-selected` before the route change fires; the hall renders
  without crashing at a 375px viewport.

## Visual acceptance (1920×1080, live dev server, Chromium via Playwright/Browser tool)

1. Six distinct physical-looking cabinets, correct per-variant proportions (curved/
   square/slim visibly different widths and heights): **YES**
2. Cabinets dominate the viewport (not shrunk into cards): **YES**
3. Gold trim, LED edge glow, jackpot LED readout, gold belly nameplate, chrome control
   deck, coin tray all visible on the baked image: **YES**
4. Live reel screen embedded and correctly aligned inside each cabinet's bezel: **YES**
   (reels come from the same `reelGrid()` preview logic as before — cosmetic in the
   hall, the real engine renders once a machine is opened, unchanged from Phase 4.0)
5. Floor reflections (flipped/faded copy of each cabinet) visible under the row: **YES**
6. Hover: cabinet scales up (~1.03–1.05), "ИГРАТЬ" label appears, neighbors dim: **YES**
7. Click: `is-selected` state applies, then navigates to `/casino/slots/:slug`
   unchanged: **YES**
8. No document vertical scroll at 1920×1080: **YES** (`scrollHeight === innerHeight ===
   1080`)
9. Mobile (375px): horizontal scroll-snap carousel, cabinets render at full detail (no
   squish), no crash: **YES**, though the vertical space above the row is not yet
   tightened for tall/short mobile aspect ratios — see limitations below.

**Honest limitation — this is a stylized/vector-illustration bake, not a photoreal
cutout.** The technique change (baked flattened image instead of live CSS) is real and
solves the *architectural* problem (a single `<img>` + one live overlay instead of an
18-node live gradient/shadow DOM tree), but the *source art* is still CSS-authored
gradients/shapes, just rendered once instead of continuously. It reads as "premium
modern cabinet illustration," not as a photograph of a physical machine. Closing that
gap needs real photographic or 3D-rendered cutout art — see below.

## FINAL_ASSET_STATUS = TEMPORARY

No image-generation tool was available in this session, and the reference photo supplied
in chat could not be exported to a file (no attachment-download tool in this
environment) — it was used only as a visual/compositional reference, not as source
pixels. The 6 cabinet PNGs and the hall background are placeholders that already use the
production architecture (transparent per-machine cutout + one background image + one
live screen overlay) and are swap-ready: replacing
`public/assets/casino/slots/cabinets/<id>.png` and `hall-bg.png` with real
photographic/3D-rendered art requires **no code change**, only re-measuring
`data-bake-screen`'s rect if the new art's screen position moves (the same
`generate-cabinet-assets.mjs` script does this automatically for baked art; for external
photos, the rect in `cabinetGeometry.generated.ts` would need the same numbers supplied
by hand or via the same Playwright measurement approach against a mock).

## Performance

- Added ~3.0 MB of PNG payload (6 cabinets ~0.25–0.35 MB each + hall background
  ~1.3 MB), all `loading="lazy"` except the hall background (`eager`, above the fold).
  No `.webp` conversion — this machine has no `cwebp`/`magick`/`sharp` available and
  macOS `sips` does not support WebP output here; PNG re-compression/WebP conversion is
  a follow-up, not a blocker.
- Runtime cost is lower than before: one `<img>` paint per cabinet instead of a live
  stack of `box-shadow`/`filter: blur()`/gradient layers recomputed continuously; idle
  animation is now 2 small overlay divs per cabinet (opacity-only) instead of animating
  LED rails, jackpot text-shadow, reel idle-bob, and glass-sweep across a much heavier
  DOM tree.

## Architectural decisions

- Cabinet body moves from live CSS/DOM to a baked image; only the reel screen (and two
  small idle-glow overlays) remain live DOM. Rejected: WebGL/Three.js hall (no 3D assets
  available yet, not needed for this interaction — static row + hover/select zoom);
  more CSS (already tried twice, hits the same ceiling).
- `.op-slots-row` moves from flexbox to CSS Grid (equal-width columns, inline
  `--slot-count`) so `aspect-ratio` sizing is deterministic per cabinet variant.
  Rejected: keeping flexbox with per-breakpoint `max-width`/`flex-basis` overrides —
  this is what caused the squish bug during implementation (an explicit width AND an
  explicit height on the same box, both definite, fight the aspect-ratio).
- Cabinet accessible name moves to `aria-label` on the link (title + jackpot), since the
  cabinet's visual text is now baked into a decorative (`alt=""`) image.
- `docs/`, test ids, routes, `slotCatalog.ts` data shape, and the slot engine are
  unchanged — this is scoped to the hall's rendering technique only.

## Build / lint / test status

- **Scoped to this sprint's files (casino/slots): clean.** `grep`-verified zero
  TypeScript errors in any `src/casino/games/slots/**` file across two full `tsc -b`
  runs; `npx vite build` (bundler only, bypassing the unrelated tsc gate below) —
  **`✓ built in 1m 54s`**, no errors, only pre-existing chunk-size/dynamic-import
  warnings unrelated to this sprint. Baked PNG assets confirmed present at
  `dist/assets/casino/slots/{hall-bg.png,cabinets/*.png}` in the production output.
- **`npm run build` / `npm run lint` for the whole `src/web` project currently fail
  before reaching the slots code**, due to **44 pre-existing TypeScript errors in
  unrelated files** not touched by this sprint: `workspace/crypto/*` (FX/DXY chart
  sprints 50.8/50.11–50.17, `useFxNativeLiveChart.tsx`), `workspace/recruiting/*`
  (email/WhatsApp/UX sprints), `workspace/agro/*`, `workspace/auto/AutoBusinessPage.tsx`,
  `src/hercules/hercules_control_center.test.ts`,
  `src/enterprise-city/odessa3d/verticalRecovery.runtime.test.ts`. Confirmed pre-existing
  (git history on those paths shows only unrelated recent sprints, e.g.
  `6eb75eb9 fix(recruiting): ...`) and reproduced identically across two independent
  fresh `tsc -b` runs. Per CLAUDE.md ("never modify unrelated modules"), these are
  **not fixed here** — flagging them is the correct scope boundary, not silently
  passing or silently fixing 40+ files in five other verticals.
- `vitest run src/casino/` (full casino suite, including the 3 new Phase 4.3 cases):
  **97/100 pass.** The 3 failures are in `casinoImmersion.test.tsx` (roulette/entrance
  "Sprint 21 visual immersion" — marble/brass/fog/lamp, room-transition veil, roulette
  table), have zero references to slots/casino cabinet code, and use the
  testing-library default 1000ms `waitFor` timeout against a lazily-loaded route in an
  environment where cold Vite/esbuild transform overhead alone is 30–100s per run (see
  duration figures on other runs in this doc) — a pre-existing flake, not a regression;
  confirmed by running the file in isolation (still fails) and confirming it imports
  nothing from `casino/games/slots/**`. Not touched, per the same scope boundary above.
  `slotsHall.test.tsx` itself: **13/13 pass**, including all 10 pre-existing assertions
  unmodified plus the 3 new Phase 4.3 cases.

## Files changed

- `src/web/src/casino/games/slots/PhysicalSlotMachine.tsx` — rewritten (image + overlay)
- `src/web/src/casino/games/slots/SlotsHall.tsx` — hall background swapped to baked image
- `src/web/src/casino/games/slots/slotsHall.css` — cabinet-shell CSS removed, ~699→~380 lines
- `src/web/src/casino/games/slots/slotsHall.test.tsx` — 3 new Phase 4.3 tests added
- `src/web/src/casino/games/slots/cabinetAssets.ts` — new (asset URL / geometry helpers)
- `src/web/src/casino/games/slots/cabinetGeometry.generated.ts` — new, auto-generated
- `src/web/scripts/casino-slots/cabinetTemplate.mjs` — new (bake template source)
- `src/web/scripts/casino-slots/generate-cabinet-assets.mjs` — new (bake pipeline)
- `src/web/public/assets/casino/slots/cabinets/*.png`, `hall-bg.png` — new, baked assets
- `.claude/launch.json` — new, dev-server preview config (enables the visual QA this
  sprint's acceptance criteria required)
- Unchanged (verified, not touched): `SlotGameScreen.tsx`, `SlotReels.tsx`,
  `slotEngine.ts`, `useSlotDemo.ts`, `slotCatalog.ts`, `slotTypes.ts`, all routing,
  `OdessaGoldMachine.tsx`, `CasinoShell.tsx`.

## What requires external assets (follow-up, not done here)

Real photoreal or 3D-rendered transparent cutouts of physical slot cabinets (per
machine or per `cabinetVariant`), and a photographic/3D-rendered hall background,
produced outside this environment (AI image generation with background removal, a
licensed 3D cabinet model rendered in Blender at the same screen-bezel geometry, or a
studio photo/render), dropped into the same file paths. No further code changes would be
needed for a straight swap; a camera/geometry mismatch would need
`cabinetGeometry.generated.ts` re-measured for the new art.
