# Interactive City 3D Architecture

Enterprise City (`/enterprise-city`, `/city`) is the platform navigation shell. The 2D CSS/DOM map remains the default view. Odessa 3D is an additive view mode that loads prepared GLB assets progressively from `public/assets/odessa/`.

## Module layout

```
src/web/src/enterprise-city/
  EnterpriseCityPage.tsx      # 2D/3D toggle, existing map preserved
  odessa3d/
    types.ts                  # CityEntity, CityRelationship, CityAsset, manifest types
    geoTransform.ts           # WGS84 ↔ scene coordinates
    assetRegistry.ts          # GLB lifecycle + dedupe
    assetLoader.ts            # Progressive GLTFLoader + procedural fallback
    tileStreaming.ts          # Camera-priority streaming + heavy-chunk hysteresis
    odessaPerformance.ts      # Demand RAF loop, adaptive DPR, visibility hysteresis
    odessaSceneController.ts  # Three.js scene (outside React state)
    Odessa3DView.tsx          # Canvas shell + layer/progress UI
    layerManager.ts           # Toggle layers without geometry reload
    cityEntityRegistry.ts     # Platform entity adapters (no CRM duplication)
    citySelection.ts          # Unified selection bus
    qualityProfile.ts         # AUTO/LOW/MEDIUM/HIGH + view mode persistence
    odessaManifest.ts         # Fetch/validate odessa_manifest.json
```

## 2D / 3D coexistence

| Mode | UI | Data |
|------|----|------|
| **2D** (default) | Existing `ec-map-shell` pan/zoom/buildings | `cityCatalog`, `cityDistricts`, graphics runtime |
| **3D** | `Odessa3DView` WebGL canvas | `odessa_manifest.json` + GLB package |
| **HYBRID** (future) | Not implemented | Architecture allows both renderers + shared `CityEntity` |

View mode is stored in `sessionStorage` (`ews_city_view_mode`). Switching modes does not destroy 2D state (viewport, focus, favorites).

## Asset pipeline

1. Blender export lives at `~/Desktop/ODESSA_WEB_EXPORT` (read-only source).
2. Copy into runtime with `python3 scripts/build_odessa_runtime_package.py`.
3. Runtime files: `src/web/public/assets/odessa/` (manifest + GLBs, nested folders preserved).
4. `loadOdessaManifest()` validates Blender web format and adapts to internal streaming tiles.
5. `ProgressiveAssetLoader` loads **REAL_GLB** only; procedural placeholders are debug-only (`VITE_ODESSA_DEBUG_PLACEHOLDER=true`).
6. GLB root transforms are preserved — no per-chunk repositioning.
7. Camera fit uses manifest `cityBounds`, refined after first real assets load.

## GeoTransform

`GeoTransform` maps WGS84 lat/lng to scene meters using manifest calibration:

- Default origin: Odessa center (46.4825, 30.7233)
- Approximate scales: 111 km/° lat, 75 km/° lng
- `calibrated: false` until survey/GPS alignment is applied

Future calibration updates only `geoTransform` in the manifest — asset URLs stay stable.

## CityEntity & platform connections

`CityEntity` is the unified selection model:

- **building** — references `cityCatalog` via `platformRef.buildingId` + route
- **project / vehicle / marker** — future kinds; store platform IDs only
- **tile / asset** — manifest geometry without duplicating CRM records

`cityEntityRegistry.seedPlatformBuildingEntities()` maps all 2D buildings to entities. Manifest assets with `entityRef` link to the same IDs.

Selection flow: raycast → `citySelection` → `EnterpriseCityPage` inspector / `openBuilding(route)`.

## Roads / routes / connections

| Concept | Type | Purpose |
|---------|------|---------|
| Physical road | `CityRelationshipKind.physical_road` | Geographic infrastructure (manifest `roads` layer) |
| Route | `route` | Dynamic transport/logistics paths (2D `streetGraph`, workflow routes) |
| Connection | `connection` | Logical links between platform entities |

These are distinct in `types.ts` and `cityEntityRegistry.listCityRelationships()`.

## Dynamic layers (future)

`LayerManager` supports `dynamic: true` layers (vehicles, IoT, weather, etc.). Dynamic objects attach to layer groups without reloading base Odessa geometry. Update via services pushing into the scene controller — not implemented in this step.

## Performance strategy (STEP 19)

- **Demand-based rendering** — single `DemandRenderLoop` RAF; renders on camera change, controls damping, asset load, resize, layer toggle — not continuously when idle
- **Adaptive pixel ratio** — LOW=1.0, MEDIUM=1.25, HIGH=1.5; AUTO degrades DPR after sustained poor frame time (~3s) with hysteresis recovery (~8s)
- **Quality profiles** control pixel ratio, antialiasing, shadows (default OFF), concurrent loads, active tile caps, load/unload distances, anisotropy
- **Frustum culling** — `mesh.frustumCulled = true` + valid bounding spheres/boxes after GLB load
- **Distance visibility** — conservative hide for distant heavy subtrees; city/coastline silhouette stays coherent
- **Heavy chunk streaming** — camera-priority scoring; load/unload hysteresis (1.4×); non-heavy tiles retained once loaded
- **Material cost** — FrontSide default, no city-wide shadows, capped anisotropy
- **ResizeObserver** — renderer resized only when container dimensions change
- **OrbitControls** — damping enabled, tuned rotate/pan/zoom speeds
- **Dev diagnostics** — optional perf panel under **Диагностика** (400ms throttle, OFF by default)
- Progressive tile/asset loading; Object3D in controller refs, not React state
- Raycast against loaded visible asset roots only

## Error isolation

- Failed GLB: logged with HTTP/parse reason, other assets continue
- Fetch validates GLB magic (`glTF`) — rejects HTML SPA fallback responses
- Loader uses per-asset fetch + parse with abort on 3D unmount
- **Important:** `Odessa3DView` must not remount on every parent render — use stable callbacks (`useCallback`) for props passed into the 3D mount effect

## Development diagnostics

When Enterprise City **Debug** overlay is on and 3D mode is active:

- **Диагностика** toggle — FPS, frame ms, draw calls, triangles, visible objects, loaded GLBs, camera distance, pixel ratio, adaptive tier (400ms throttle)
- **3D Debug** JSON — loaded/queued/failed counts, triangle stats, camera position, city bounds
- Tile bounds overlay (dev only)

## Connecting future platform modules

1. Register a `CityEntity` with `platformRef: { module, entityId, route }`.
2. Optionally add manifest asset with matching `entityRef` or geo bounds.
3. Subscribe to `citySelection` or push updates into a dynamic layer.
4. Do not store project/CRM payloads inside the map module — reference IDs only.

## Related docs

- `docs/ENTERPRISE_CITY.md` — Enterprise City product scope
- `docs/ENTERPRISE_CITY_RENDERING_ARCHITECTURE.md` — 2D graphics engine
- `docs/REGIONAL_DIGITAL_TWIN.md` — Odessa spatial runtime seed
