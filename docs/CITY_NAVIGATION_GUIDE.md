# Enterprise City — Navigation Guide

**Sprint:** CG-5 — Research & Specification only. No source code was modified.

**Do not duplicate:** `ENTERPRISE_NAVIGATION.md` is the platform-wide navigation philosophy and the
authority on Command Palette, global search, Sidebar, Dock, and shortcut mechanics — this document
does not restate any of it, only how City specifically plugs into (and, in three places, duplicates)
that real system. `NAVIGATION_IMPROVEMENTS.md` items are referenced by ID (`NAV-##`), not re-described.

## 1. Building selection (real)

Click or `Enter`/`Space` on a `.ec-building` tile → `openBuilding()` → real navigation. Buildings are
native `<button>` elements (real, `CityBuildingTile`), so basic keyboard activation and Tab order
already work without any custom key handling — but **no arrow-key spatial navigation exists** (see
§3). Hover and focus both call the same handler today (`onFocus={onFocus}` wired to both
`onMouseEnter` and `onFocus` — real, `EnterpriseCityPage.tsx`), which means keyboard-Tabbing through
buildings currently produces the exact same visual reaction (hover pulse + `focusId` change) as mouse
hovering — a deliberate simplicity, not a gap, but worth naming so a future accessibility pass doesn't
"fix" it into two different treatments without reason.

## 2. District switching (real)

Two real entry points: the district quick-jump chip row (`.ec-quick-jump`, always visible) and
clicking a district's floating label on the map itself (`.ec-district-label`). Both call the same real
`jumpDistrict()` → animated camera focus (CG-3) + `district_activation` flash (CG-3/CG-2). District
switching always resolves to "the first building in that district" (real, `CITY_BUILDING.find(b =>
b.district === id)`) — there is no district-level landing view distinct from its first building.
**SPEC note**: this is a reasonable simplification today at 34 buildings, but worth revisiting if
`CITY_SIMULATION.md` §1's proposed `DistrictRuntimeSummary` aggregation ever gets a visual home — a
natural district-switch destination would then be a summary view, not an arbitrary first building.

## 3. Keyboard navigation (mostly SPEC — real gap)

**Real today:** Tab order through buttons (native), `Enter` in the search input opens the top hit
(real, `onKeyDown` handler), `Escape` presumably closes overlays platform-wide (`ENTERPRISE_NAVIGATION.md`'s
global shortcut list) but City registers no City-specific keyboard shortcuts of its own.

**SPEC — proposed grid navigation:** Arrow keys move focus between buildings using their real `x`/`y`
percentage coordinates (`CityBuilding.x/y`, already the real layout data) to resolve "nearest building
in that direction" — no new spatial index needed, a simple nearest-neighbor scan over the already-tiny
34-building catalog. `Home`/`End` jump to Plaza / the last-focused building. This is the single
highest-value item in this document for `CITY_ACCESSIBILITY.md` §1 (keyboard-only usage) — flagged
here and cross-referenced there rather than specified twice.

## 4. Search (real, local + global)

Two real result sources render in the same `.ec-search-panel`: `searchBuildings(q)` (City-local, matches
building label/tokens) and `searchProvider.search(q)` (the real, platform-wide index —
`ENTERPRISE_NAVIGATION.md`'s ~70-document static corpus). City buildings and districts are already
**registered into that global index** on mount (`registerCitySearchDocs()`, real, runs once per City
page load) — meaning a City building is findable from the platform-wide Command Palette too, not only
from City's own search box. This is a genuine positive integration point, not a gap.

## 5. Command Palette (real elsewhere, not City-specific — one integration gap)

City does not implement its own palette — it relies entirely on the platform's real, single live
Command Palette (`UniversalCommandPalette.tsx`, per `ENTERPRISE_NAVIGATION.md`'s finding that the
*other* copy, `navigation/components/CommandPalette.tsx`, is dead code, tracked as `TD-40`). **This
document takes no position on TD-40** — it is a platform-wide defect, not a City-specific one, and
fixing it is out of this document's scope. The one City-specific gap: City buildings are searchable
from the Palette (§4), but there is no Palette-specific *action* category for City (e.g. "Focus
district: Finance" as a directly-executable command distinct from "navigate to a route") — **SPEC**:
a small `registerCityPaletteActions()` alongside the existing `registerCitySearchDocs()`, feeding
`jumpDistrict`/`focusBuildingAnimated` as real callable actions, not just navigable search hits.

## 6. Desktop integration (real — corrected from this document's first draft)

> **Correction:** an earlier version of this section stated City "is not observed to be openable as a
> literal Desktop window." Deeper research for `CITY_DESKTOP.md` (Sprint CG-6) found this was wrong —
> City genuinely does open as a real Desktop window. Left here, struck through in spirit, rather than
> silently edited, per this engagement's own practice of correcting rather than erasing prior claims.

City carries a real, explicit escape hatch back to the OS shell: the header's `Desktop OS` link
(`<Link to="/desktop">`, real, always visible). City is itself reachable from the Desktop
Launcher/Dock (`desktopCatalog.ts` has a real `{ id: "city", path: "/enterprise-city" }` entry) —
**and City genuinely does open as a real Desktop window**: `WindowFrame.tsx` renders every Desktop
window as an `<iframe src="{path}?embed=1">`, which for City resolves to
`/enterprise-city?embed=1`, triggering `WorkspaceLayout`'s real embed branch (chrome-free render).
Full architecture and the consequences of the iframe boundary are specified in
[`CITY_DESKTOP.md`](./CITY_DESKTOP.md) §2 — not repeated here.

## 7. Breadcrumbs (real, but a second parallel implementation — flagged)

City renders its own breadcrumbs via `cityNavigation.breadcrumbs(focused)` (real,
`cityNavigation.ts`) — a City building's breadcrumb is always exactly `Enterprise City / {district} /
{building label}`, three levels, fixed shape. `ENTERPRISE_NAVIGATION.md` separately documents a real,
platform-wide `breadcrumbEngine.ts` that derives breadcrumbs from the URL pathname for every other
route in the app. **These are two independent breadcrumb systems** — City's is not built on top of
`breadcrumbEngine.ts`, it is a second, purpose-built implementation. This document flags it rather than
silently treating it as fine: unlike the favorites/history triplication (§9), this one is arguably
justified (a URL-pathname-derived breadcrumb genuinely cannot express "which district a building
belongs to," since that's not part of the route), so this document's recommendation is **document the
justification, not merge the two** — but a future navigation audit should confirm that reasoning still
holds rather than this being assumed permanently correct.

## 8. Deep linking (real)

`?building={id}` query param, handled in a real `useEffect` — on load, sets `focusId` and pans the
camera to that building (currently an instant pan, not animated — a candidate for `CITY_CAMERA.md` §1
`focusBuildingAnimated`, since CG-3 already exists and this is the one remaining call site in
`EnterpriseCityPage.tsx` still using the raw un-animated `panToBuilding`). `?embed=1` (real) suppresses
chrome for embedded contexts (§6). No deep link exists yet for **district** (only building) or for a
specific **camera viewport** (only `ews_city_viewport_v1` session state, not shareable via URL) —
**SPEC**: `?district={id}` as a direct analog to `?building=`, and (**lower priority**, no product need
identified yet) a `?viewport=x,y,zoom` for sharing an exact camera framing, e.g. in a support/demo link.

## 9. History (real — one of three parallel implementations, most-correct)

`cityNavigation.history()`/`pushHistory()` — real, persists to **`localStorage`**
(`ews_city_history_v1`, up to 24 entries) — genuinely the most durable of the navigation-memory systems
`ENTERPRISE_NAVIGATION.md` catalogued platform-wide (its two systems, `navigation/managers/*` and
`workspace/managers/*`, **do not** persist to `localStorage`, tracked `TD-41`). City's is the one
real exception to that defect. See §11 for why this is still flagged as a duplication concern despite
being individually well-built.

## 10. Favorites (real — persists, and partially bridges to the shared system)

`cityNavigation.toggleFavorite()`/`favorites()`/`isFavorite()` — real, persists to `localStorage`
(`ews_city_favorites_v1`). On toggle, it also calls the real, shared `favoritesManager.add()`/
`.remove()` (`navigation/managers/favoritesManager.ts`) — so a City favorite **does** appear in the
platform-wide Favorites list. This bridge is **one-directional**: toggling or removing a favorite from
the platform-wide list does not update `cityNavigation`'s own `ews_city_favorites_v1` store, so
`isFavorite()` inside City could disagree with the platform's own favorites list after an
out-of-City removal. Flagged as a precise, real inconsistency (not a guess) — **SPEC fix**: City's
`isFavorite()` should read from the shared `favoritesManager` as its source of truth (checking for
`city_{id}` presence) instead of maintaining a second boolean in `ews_city_favorites_v1`, collapsing
the write-only bridge into a real single source of truth.

## 11. Pinned buildings

The brief's "Pinned buildings" is the same real capability as §10's Favorites — `cityNavigation`
exposes no separate "pin" concept beyond favorite/not-favorite. This document does not propose a
distinct Pinned mechanism (favorites already do what pinning would); `CITY_BUILDING_STATES.md` §3.4
already names the tile-level `is-pinned` visual marker this document's own `CITY_USER_JOURNEYS.md`
persona table assumes managers rely on daily.

### 11.1 The triplication this section surfaces (for Cursor)

Three independent "recent/favorite/history" systems now exist platform-wide:
`navigation/managers/{favoritesManager,navigationHistory}.ts` (real, **not** persisted — `TD-41`),
`workspace/managers/{favoritesManager,recentActivity}.ts` (real, **not** persisted — same `TD-41`),
and `enterprise-city/cityNavigation.ts` (real, **is** persisted, one-way-bridged into the first). This
document does not recommend City give up its own system (it is the best-built of the three and City's
shape — building IDs, not arbitrary pages — doesn't map cleanly onto the other two's generic-page
model) but recommends `TD-41`'s eventual fix use City's `localStorage` persistence pattern as the
reference implementation, and that §10's one-directional bridge be closed in the same pass.

## Related documents

`ENTERPRISE_NAVIGATION.md` (platform navigation authority), `NAVIGATION_IMPROVEMENTS.md`
(`NAV-##` tracked items), `TECH_DEBT.md` (`TD-40` dead Command Palette, `TD-41` unpersisted
favorites/history), `CITY_ACCESSIBILITY.md` §1 (keyboard grid navigation, specified once there),
`CITY_CAMERA.md` (the animated focus functions §8's deep-link improvement would call).
