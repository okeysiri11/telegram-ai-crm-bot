# Regional Digital Twin — Territory Model, Multi-City Architecture & Expansion Framework

**Sprint:** CQ-16 — Architecture Research + Geospatial Modeling. Documentation only, `src` not
modified.

**Do not duplicate:** This document's single most important finding is that it is **not** a greenfield
problem. `docs/SPATIAL_RUNTIME.md` (real, Sprint 29.4, package `src/web/src/runtime/spatialRuntime`)
already implements almost exactly the brief's §1 Territory Model — a real `SpatialEntity` hierarchy
(`Country → Region → City → District → Street → Building → Floor → Room → Workspace`, plus `Zone`,
`POI`, `Virtual Space`), real WGS84-approximate coordinates seeded for Ukraine → Odesa Oblast → Odessa,
real routing (Dijkstra over a connected-building graph, haversine distance), real permission scopes,
and a real EventBus integration. This document's job is to (a) map the brief's territory vocabulary
onto that real model precisely, (b) name the one genuine gap — **the runtime is architecturally
generic but seeded for exactly one city** — and (c) design the Expansion Framework that closes it,
without proposing a second spatial engine. `docs/CITY_LIVING_ECONOMY.md` §2.1 (CQ-10) previously found
"the real system today has no actual Odessa geography encoded in it" — **that finding is now
superseded by real Sprint 29.4 work** and is corrected here, not silently left stale.

## 0. What is real today (verified, Sprint 29.4)

| Real symbol | Shape | File |
|---|---|---|
| `SpatialEntityKind` | `country \| region \| city \| district \| street \| building \| floor \| room \| workspace \| zone \| poi \| virtual_space` | `spatialTypes.ts:23-35` |
| `SpatialDistrictKind` | `business \| industrial \| logistics \| financial \| medical \| education \| construction \| marketplace \| residential \| custom` | `spatialTypes.ts:37-47` |
| `ODESSA_CITY` | real seed constant — `lat: 46.4825, lng: 30.7233`, `country: "UA"`, `region: "Odesa Oblast"` | `spatialTypes.ts:11-21` |
| `spatialRegistry` | real in-memory entity/relationship store — `upsert/get/list/children/ancestors/contains/adjacent/connected` | `spatialRegistry.ts` |
| `routingEngine` | real Dijkstra + haversine distance/travel-time, walk/vehicle/transit/virtual modes | `routingEngine.ts` |
| `spatialPermissions` | real ranked scopes: `public < citizen < company < assigned < enterprise_admin` | `spatialPermissions.ts` |
| `seedOdessaSpatial()` | the one hardcoded seed function — projects `cityCatalog.ts`/`cityDistricts.ts` into the hierarchy, single city only | `spatialSeed.ts` |
| API | `/api/enterprise-spatial/v1`, UI `/spatial`, events `LocationChanged`/`EnteredBuilding`/`EnteredDistrict`/`BuildingRegistered`/etc. published as `spatial_runtime_update` | `spatialTypes.ts:8`, `SPATIAL_RUNTIME.md` |

`spatialRuntime.ts` already wires this to real `businessNetworkEngine`, `digitalCitizenEngine`,
`lifeEngine`, and `assetRuntime` on startup (`spatialRuntime.ts:100-105`) — Business Network and
Digital Citizen presence are already spatially anchored, not a new integration this document invents.

## 1. Territory Model — brief's eleven items mapped onto the real hierarchy

| Brief term | Status | Real/SPEC mapping |
|---|---|---|
| Country | **Real** | `SpatialEntityKind: "country"` — one instance seeded, `country_ua` |
| Region | **Real** | `SpatialEntityKind: "region"` — one instance seeded, `region_odesa` |
| City | **Real** | `SpatialEntityKind: "city"` — one instance seeded, `city_odessa` |
| District | **Real** | `SpatialEntityKind: "district"`, 12 real City districts + 3 Sprint-29.4 extensions (logistics/medical/residential) |
| Business Zone | **Real** | `SpatialDistrictKind: "business"` (maps to the real `enterprise` City district, `spatialRegistry.ts:37`) |
| Industrial Zone | **Real** | `SpatialDistrictKind: "industrial"` (maps to `erp`/`production`, `spatialRegistry.ts:42-43`) |
| Technology Park | **Naming mismatch, not missing** | The real `developer`/`ai` City districts are mapped to `SpatialDistrictKind: "construction"` (`spatialRegistry.ts:50-51`) — a real but confusing choice for what the brief calls a Technology Park. Recommend a new literal, `"technology_park"`, added to the `SpatialDistrictKind` union (additive, non-breaking) and re-pointing `developer`/`ai` to it — a rename, not a new modeling concept |
| Logistics Hub | **Real** | `SpatialDistrictKind: "logistics"`, already a seeded district (`spd_logistics`, `spatialSeed.ts:52`) |
| Port Area | **Partially real, under-modeled** | A real `poi` (`spo_port`, "Odessa Port Gate", `spatialSeed.ts:194-200`) exists as a *point*, not a zone, inside the Logistics district. Recommend promoting `"port"` to a first-class `SpatialDistrictKind` for cities with substantial port real estate, backed by the real `applications/port_erp` (AIS/GPS/geofence, real lat/lng) and `applications/port_enterprise` (warehouse/multimodal logistics) data — reusing existing port engines, not inventing new port modeling |
| Special Economic Zone | **New — genuinely absent** | No real precedent anywhere in the codebase. SPEC: a new `SpatialDistrictKind: "special_economic_zone"` whose only structural addition is a `metadata.regulatoryProfileId` pointer (see §4, Regulatory Profiles) — no new entity type, no new engine |
| Custom Territories | **Real** | `SpatialDistrictKind: "custom"` is already the real fallback default (`districtKindForCityDistrict()`'s `default:` case, `spatialRegistry.ts:55-56`) |

**Net finding:** of the brief's 11 territory concepts, **7 are already real**, 1 is a real-but-misnamed
mapping (Technology Park), 1 is real-but-under-modeled (Port Area, a POI not a zone), and only 1
(Special Economic Zone) requires a genuinely new concept — and even that is additive (one new enum
value + one metadata pointer), not a new subsystem.

## 2. Multi-City Architecture — the one real gap

### 2.1 What's generic vs. what's hardcoded

The **data model** (`SpatialEntity`, the registry, routing, permissions) has no single-city assumption
baked in anywhere — `spatialRegistry` is a plain `Map` keyed by entity id, `kind: "city"` is one value
among many, and nothing in `spatialRegistry.ts`/`routingEngine.ts` special-cases Odessa. The **seed
data** is the hardcoded part: `seedOdessaSpatial()` (`spatialSeed.ts`) is a single, literal function —
Ukraine/Odesa Oblast/Odessa/12 districts/34 buildings/3 streets, all inlined — with no parameter, no
loop over a list of cities, and no second call anywhere in the codebase. `spatialRuntime.startup()`
calls it exactly once, unconditionally (`spatialRuntime.ts:104`).

**Conclusion, stated precisely so a future implementation sprint doesn't over-scope this**: adding a
second city is not a runtime redesign — it's writing a second seed function with the same shape as
`seedOdessaSpatial()`, called against the same generic registry. The brief's own instruction ("new
cities should plug into the same Runtime") is already true structurally; it just hasn't been exercised
with more than one input yet.

### 2.2 `TerritoryProfile` — the SPEC generalization

```ts
// SPEC — generalizes seedOdessaSpatial()'s inline literals into reusable input data.
// Does not change SpatialEntity, spatialRegistry, or routingEngine — only adds a data layer
// that seedOdessaSpatial() itself becomes one (default) instance of.
interface TerritoryProfile {
  countryId: string;              // e.g. "country_ua" — reuse if the country already exists
  countryName: string;
  regionId: string;
  regionName: string;
  cityId: string;
  cityName: string;
  cityNameLocal?: string;
  center: { lat: number; lng: number };
  timezone: string;
  districts: {
    id: string;
    name: string;
    districtKind: SpatialDistrictKind;   // real type, spatialTypes.ts
    x: number; y: number;                 // city-plane position, same convention as CityDistrict
  }[];
  // Buildings/streets are intentionally NOT part of this profile — City districts still own
  // their own building catalog (cityCatalog.ts); a second city needs its own City catalog entry
  // before it can be spatially seeded, which is the correct dependency direction (City owns
  // "what exists," Spatial Runtime owns "where it is").
}
```

`seedOdessaSpatial()` becomes, under this design, the literal `TerritoryProfile` for Odessa — no
behavior change for the existing city, and every one of the brief's example cities (Kyiv, Lviv,
Warsaw, Dubai, Berlin) is a second, third, fourth… profile fed to one generic
`seedTerritory(profile: TerritoryProfile)` function, replacing the single hardcoded function without
touching its real internals (`spatialRegistry.upsert`/`.contains`/`planeToGeo`).

### 2.3 Multi-country note

`country` and `region` are already generic `SpatialEntityKind` values — a second country (e.g. Poland,
for Warsaw) is just a second `TerritoryProfile.countryId` that doesn't already exist in the registry.
No design change is needed beyond §2.2; this section exists only to confirm the brief's "without
redesign" requirement is met at the country level too, not only the city level.

## 3. The "Digital Twin" naming collision — a fifth entry, not a rename of this document

`docs/ARCHITECTURE_MAP.md` §13 already documents a real four-way naming collision on "Digital Twin":
`platform_enterprise_digital_twin/` ("Enterprise Digital Twin 2.0," `EnterpriseDigitalTwinLibrary`,
`/api/enterprise-etw/v1`), legacy **EDT** (the predecessor it supersedes), `applications/
executive_center/twins.py`'s generic `DigitalTwinEngine`, and `applications/platform_builder/
digital_twin/`'s read-only reflection layer. **All four are false friends relative to this brief**:
every one of them models a single company's org chart, processes, resources, or AI state
(`platform_enterprise_digital_twin/models.py:39`'s own `"one_twin_per_company"` principle is explicit
about this) — **none has any geospatial or territory concept**. The real geo-relevant lineage is a
fifth, structurally separate thing: Enterprise City + Spatial Runtime, which `docs/SPATIAL_RUNTIME.md`
itself already brands "Odessa (Одеса) Digital Twin."

This sprint's brief is titled "Regional Digital Twin," which — read literally — would deepen a
five-way collision on a term that already means four different non-geographic things in this codebase.
**Recommendation**: keep using "Digital Twin" only in the narrative/brand sense Sprint 29.4 already
established ("Odessa Digital Twin," a City/Spatial-Runtime phrase), and use **"Territory"** or
**"Regional Spatial Twin"** as the structural/technical term in code, API names, and future doc
titles — exactly as this document's own filename does. `docs/ARCHITECTURE_MAP.md` §13 is updated
(alongside this document) to record this as the fifth instance of the collision, with the
disambiguation rule stated explicitly so a future sprint doesn't have to re-derive it.

## 4. Expansion Framework — how a new territory is added (brief §8)

All six brief items reduce to operations on `TerritoryProfile` (§2.2) plus the real City catalog it
depends on — no new subsystem:

| Brief item | Design |
|---|---|
| Import | A `TerritoryProfile` is a plain data object — "import" means constructing one (from a form, a config file, or an admin tool) and calling `seedTerritory(profile)` once |
| Configuration | The profile itself *is* the configuration — no separate config layer |
| District Templates | A `SpatialDistrictKind` + a default building mix is a template; §1's zone-kind table is the starting template set (Business/Industrial/Technology Park/Logistics Hub/Port/SEZ/Custom) |
| Localization | `cityNameLocal`/`regionName` fields already anticipated in `TerritoryProfile`; mirrors the real `ODESSA_CITY.nameUk` precedent (`spatialTypes.ts:14`) |
| Regulatory Profiles | **New, SPEC** — a `RegulatoryProfile` referenced by SEZ (and optionally any) districts via `metadata.regulatoryProfileId`; deliberately kept as an opaque reference here, not fleshed into a compliance engine — a future sprint's job, cross-referencing the real `ComplianceVerificationLevel`/`ComplianceRiskProfile` (CQ-10) rather than inventing a parallel one |
| Business Categories | Real `BusinessProfile.category` (Sprint 29.0, `EBN` facade) already exists per-company; a territory's "business categories" is a read aggregate over real `BusinessProfile`s located in that territory (via `LocationAssignment`), not a new taxonomy |

## Non-goals

- No new spatial/geospatial engine — every real capability in §0 is reused as-is.
- No coordinate-system change — `planeToGeo()`'s percentage-space-to-approximate-WGS84 projection is
  reused unchanged for every additional city, per its own existing per-city-center math.
- No new building/company/citizen model — `TerritoryProfile` seeds the existing `SpatialEntity`
  hierarchy; it does not introduce a parallel one.
- No resolution of the "Digital Twin" naming collision by renaming the four real false-friend
  packages — out of scope for a documentation-only sprint; §3 only prevents a fifth collision going
  forward.

## Related documents

`docs/SPATIAL_RUNTIME.md` (real, Sprint 29.4, the foundation this entire document extends),
`docs/CITY_DISTRICTS.md` (CG-9, real 12-district catalog), `docs/CITY_LIVING_ECONOMY.md` §2.1 (CQ-10,
corrected by §0 above), `docs/ARCHITECTURE_MAP.md` §13 (Digital Twin collision, extended this sprint),
`docs/ENTERPRISE_BUSINESS_NETWORK.md` (Sprint 29.0, real `BusinessProfile.category`),
`docs/TERRITORIAL_GOVERNANCE.md`, `docs/REGIONAL_ECONOMY.md`, `docs/SMART_INFRASTRUCTURE.md`,
`docs/TERRITORIAL_ANALYTICS.md`, `docs/DIGITAL_TWIN_STANDARDS.md` (CQ-16 siblings).
