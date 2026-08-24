# STEP 28 — Odessa 3D interaction layer (picking + highlight + entity binding)

## Status

Shipped a cached pick registry, throttled hover raycasts, click-vs-drag selection, material-safe per-mesh highlights, and exact-only Enterprise City binding. Original GLBs, CRM datasets, physics, GIS reconstruction, and STEP 20–27 runtime behavior are unchanged. STEP 29 was **not** started.

## SCENE AUDIT

Runtime hierarchy after attach (unchanged from STEP 22–27):

```
scene
  odessaCityRoot
    layer_city | layer_heavy | layer_dynamic
      <assetId> Group          ← one per active GLB
        Mesh / Group from GLB
  tile_debug / pick_debug      ← helpers only
```

Live counts are not assumed at build time. After GLBs activate, Диагностика reports `sceneAudit` + INTERACTION.pickables.

From the authored package (not a Mesh=building assumption):

| Fact | Value |
|---|---|
| Manifest assets | **45** GLBs |
| Typical authored `objects` | tens per tile (e.g. TILE_02_00 = 34) |
| Mesh ≠ building | **yes** — CAD/OSM tiles contain roads, vegetation, fragments |
| `entityRef` in manifest | **none** |
| Identifiable asset ids | tile ids (`TILE_02_00`, REST batches, heavy chunks) |
| Mesh userData after register | `odessaAssetId` stamped; materials may have `odessaMaterialClass` / intern flags |
| Shared materials | intern cache reuses untextured `MeshStandardMaterial` instances |

Water-like meshes are excluded from pickables. Unnamed meshes still get a deterministic `pick:<asset>:<index>:unnamed` id.

## PICKABLE OBJECTS

`PickableEntity` is cached once when an asset becomes **active**, not per frame.

- Deterministic `pickId` = `pick:{assetId}:{meshIndex}:{sanitizedName}`
- No `Math.random`; Three.js `uuid` is stored only as `objectUuid` for session lookup
- Duplicate `registerAsset` unregisters first
- Unload / 2D remount `clear()` drops all Object3D refs

## RAYCAST STRATEGY

- Hover: throttled **~18/s** (`55ms`), only while pointer is inside the canvas, skipped during `INTERACTING`
- Click: one event-driven raycast on primary `pointerup`
- NDC from the canvas bounding rect
- Candidates = registered pickable meshes only (not the full scene)
- If candidates > 600, asset AABB broad-phase first
- **Not** called from the render loop

## HOVER

- Top valid hit → `hoveredPickId`
- Same target does not re-apply materials
- Canvas leave clears hover
- Original interned materials are never mutated

## SELECTION

React / city state stores **IDs**, not Object3D.

- Click mesh: persist selection through orbit / pan / zoom
- Empty click / ESC: clear
- Another mesh: move selection
- Unloaded GLB: drop the Three.js ref, keep pick metadata, UI says **«Объект сейчас не активен»**
- Re-activate same asset: deterministic ids restore the highlight

## HIGHLIGHT METHOD

**A. temporary per-object material clone** (chosen).

Shared interned materials made B (overlay mesh) and C (edges) unnecessary extra draw cost. Clone is assigned only on the hit mesh; maps stay shared; clones are disposed on restore.

- Hover: soft `#3ecfad` emissive (EDS light primary)
- Selected: stronger `--eds-primary` (`#0f6a5a`) emissive
- Selected wins if hover and selection are the same mesh

## SHARED MATERIAL SAFETY

Two meshes sharing one interned material: only the target gets a clone. The neighbor still points at the original. Tests cover isolation + full restore (`materialCloneCount` → 0).

## ENTITY BINDING

`odessa3d/interaction/entityBinding.ts` reuses `cityCatalog` / `cityEntityRegistry` / `CITY_STATUS_SEED`. No new CRM copy.

Exact sources only: `entityRef` / `entityRefs`, exact `assetId`, exact `meshName`, `MANUAL_ODESSA_ENTITY_MAP`.

Results: **BOUND** | **UNBOUND** | **AMBIGUOUS**.

No fuzzy names, no invented address / owner / company / CRM status.

## BOUND COUNT

**0** for current Odessa GLBs (no `entityRef`, tile ids are not catalog building ids, manual map is empty).

## UNBOUND COUNT

**All registered pickable meshes** until a real mapping is authored. Typical session = every non-water mesh in active tiles.

## UI

- Toolbar **«Выбор объектов»** default **ON** in 3D
- Selected-object badge in the toolbar
- Compact right-side panel:
  - BOUND: catalog name, type, existing status label, module, **«Открыть объект»** (existing `navigate` route)
  - UNBOUND: «3D объект» + asset / mesh / layer / class + **«Нет связи с объектом Enterprise City»**
  - `pickId` only when Диагностика is on
- **Фокус** / **Сброс**
- Диагностика INTERACTION + optional BOX3 helper (default off)

## CAMERA CLICK CONFLICT

`pointerdown` + `pointerup` + **8px** threshold. Orbit/pan/trackpad movement sets `clickMoved` and does not select on release.

## FOCUS

Double-click or panel **Фокус**: world AABB of the picked mesh, ease-out 420ms reframe along current view direction, camera stays **outside** the box (`y ≥ box.max.y + margin`), clip range reused from STEP 20/21 helpers.

## 2D / 3D

- 3D → 2D: dispose restores cloned materials, clears registry, drops listeners / raycaster
- BOUND city selection remains in `citySelection` for 2D
- UNBOUND never writes a fake building into 2D
- 2D → 3D: new controller, registry rebuilt only from assets that activate again; no duplicate listeners

## PERFORMANCE IMPACT

- No per-frame React updates (hover stays in Three.js; HUD polls only with Диагностика)
- No per-frame scene walk / material clone
- Hover raycast throttled; click event-driven
- Registry cached; candidate broad-phase above 600 meshes

Camera / water / fog / lighting / LOD / streaming paths were not rewritten.

## FILES CHANGED

| File | Role |
|---|---|
| `src/web/src/enterprise-city/odessa3d/interaction/*` | Pick registry, IDs, raycast meter, gestures, highlight, binding, audit, focus, panel |
| `src/web/src/enterprise-city/odessa3d/odessaSceneController.ts` | Register on activate, unregister on unload, hover/click/ESC/focus |
| `src/web/src/enterprise-city/odessa3d/Odessa3DView.tsx` | Toggle, panel, diagnostics INTERACTION |
| `src/web/src/enterprise-city/odessa3d/types.ts` | Interaction + sceneAudit diagnostics |
| `src/web/src/enterprise-city/odessa3d/index.ts` | Exports |
| `src/web/src/index.css` | Object panel layout |
| `docs/STEP_28_ODESSA_3D_INTERACTION_RESULT.md` | This report |

## TESTS

`npm test -- src/enterprise-city` — **199 passed** (was 185).

Coverage: pick registry, deterministic IDs, duplicate register, unload cleanup, 2D/3D remount clear, click-vs-drag threshold, hover/selection ID transitions, shared-material isolation, BOUND / UNBOUND / AMBIGUOUS, focus outside AABB.

## BUILD

`npx vite build` — **PASS** (17.3s).

## KNOWN LIMITS

- One Mesh is still not one real-world building; picking is geometric, not cadastral.
- Almost every Odessa GLB is UNBOUND until manifest `entityRef` or the manual map is authored.
- Hover is skipped while the camera is in `INTERACTING` (high-speed orbit/pan).
- Live Safari mesh counts were not measured from this session; use Диагностика INTERACTION / sceneAudit on the machine.
- No SSAO, physics, GIS, or fake identities.

## STEP 29 STARTED: NO
