/**
 * 3D PickableEntity → existing Enterprise City entity.
 * Exact matches only. Never invent company, address, owner, or CRM status.
 */

import { CITY_BUILDINGS, CITY_STATUS_SEED, getBuilding, type CityBuildingId } from "../../cityCatalog";
import { getCityEntity } from "../cityEntityRegistry";
import { MANUAL_ODESSA_ENTITY_MAP } from "./manualEntityMap";
import type { EntityBindingResult, PickableEntity } from "./types";

const BUILDING_IDS = new Set<string>(CITY_BUILDINGS.map((b) => b.id));

export type BindingLookupInput = {
  pickId: string;
  assetId: string;
  meshName?: string;
  entityRefs?: string[];
  manifestEntityRef?: string;
  manualMap?: Readonly<Record<string, CityBuildingId>>;
};

function exactBuildingId(value: string | undefined | null): CityBuildingId | undefined {
  if (!value) return undefined;
  if (!BUILDING_IDS.has(value)) return undefined;
  return value as CityBuildingId;
}

/**
 * Collect exact catalog hits. Conflicting ids → AMBIGUOUS.
 * No substring / Levenshtein / geo guessing.
 */
export function collectExactBuildingIds(input: BindingLookupInput): CityBuildingId[] {
  const map = input.manualMap ?? MANUAL_ODESSA_ENTITY_MAP;
  const hits: CityBuildingId[] = [];
  const add = (id: CityBuildingId | undefined) => {
    if (id && !hits.includes(id)) hits.push(id);
  };

  add(exactBuildingId(input.manifestEntityRef));
  for (const ref of input.entityRefs ?? []) add(exactBuildingId(ref));
  add(exactBuildingId(input.assetId));
  add(exactBuildingId(input.meshName));
  add(exactBuildingId(map[input.assetId]));
  if (input.meshName) add(exactBuildingId(map[input.meshName]));
  return hits;
}

export function bindPickableFromLookup(input: BindingLookupInput): EntityBindingResult {
  const hits = collectExactBuildingIds(input);
  if (hits.length === 0) {
    return {
      status: "UNBOUND",
      pickId: input.pickId,
      assetId: input.assetId,
      reasons: ["no_exact_entity_mapping"],
    };
  }
  if (hits.length > 1) {
    return {
      status: "AMBIGUOUS",
      pickId: input.pickId,
      assetId: input.assetId,
      reasons: [`conflicting_ids:${hits.join(",")}`],
    };
  }

  const buildingId = hits[0];
  const building = getBuilding(buildingId);
  const cityId = `city_building_${buildingId}`;
  const city = getCityEntity(cityId);
  const live = CITY_STATUS_SEED[buildingId];

  return {
    status: "BOUND",
    pickId: input.pickId,
    assetId: input.assetId,
    enterpriseEntityId: cityId,
    buildingId,
    label: building?.label ?? city?.label,
    kind: city?.kind ?? "building",
    route: building?.route ?? city?.platformRef?.route,
    module: city?.platformRef?.module ?? "enterprise-city",
    statusLabel: live?.processLabel,
    reasons: ["exact_catalog_id"],
  };
}

export function bindPickableEntity(
  pickable: PickableEntity,
  extra?: Pick<BindingLookupInput, "entityRefs" | "manifestEntityRef" | "manualMap">,
): EntityBindingResult {
  return bindPickableFromLookup({
    pickId: pickable.pickId,
    assetId: pickable.assetId,
    meshName: pickable.meshName,
    entityRefs: extra?.entityRefs,
    manifestEntityRef: extra?.manifestEntityRef,
    manualMap: extra?.manualMap,
  });
}

export function bindingCounts(results: Iterable<PickableEntity>): {
  bound: number;
  unbound: number;
  ambiguous: number;
} {
  let bound = 0;
  let unbound = 0;
  let ambiguous = 0;
  for (const p of results) {
    if (p.bindingStatus === "BOUND") bound += 1;
    else if (p.bindingStatus === "AMBIGUOUS") ambiguous += 1;
    else unbound += 1;
  }
  return { bound, unbound, ambiguous };
}
