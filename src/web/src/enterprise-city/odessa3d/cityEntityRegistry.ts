/**
 * City entity registry + platform adapters.
 */

import { CITY_BUILDINGS } from "../cityCatalog";
import { ODESSA_CITY } from "@/runtime/spatialRuntime/spatialTypes";
import { planeToGeo } from "@/runtime/spatialRuntime/spatialRegistry";
import type { CityEntity, CityRelationship, OdessaManifest } from "./types";

const entities = new Map<string, CityEntity>();
const relationships = new Map<string, CityRelationship>();

export function clearCityEntities() {
  entities.clear();
  relationships.clear();
}

export function registerCityEntity(entity: CityEntity): CityEntity {
  entities.set(entity.id, entity);
  return entity;
}

export function getCityEntity(id: string): CityEntity | undefined {
  return entities.get(id);
}

export function listCityEntities(): CityEntity[] {
  return [...entities.values()];
}

export function registerCityRelationship(rel: CityRelationship): CityRelationship {
  relationships.set(rel.id, rel);
  return rel;
}

export function listCityRelationships(kind?: CityRelationship["kind"]): CityRelationship[] {
  const rows = [...relationships.values()];
  return kind ? rows.filter((r) => r.kind === kind) : rows;
}

/** Seed platform buildings as CityEntity references (no duplicate CRM data). */
export function seedPlatformBuildingEntities() {
  for (const b of CITY_BUILDINGS) {
    registerCityEntity({
      id: `city_building_${b.id}`,
      kind: "building",
      label: b.label,
      geo: planeToGeo(b.x + b.w / 2, b.y + b.h / 2),
      platformRef: {
        module: "enterprise-city",
        entityId: b.id,
        route: b.route,
        buildingId: b.id,
      },
      metadata: { district: b.district, short: b.short },
    });
  }
  registerCityEntity({
    id: ODESSA_CITY.id,
    kind: "marker",
    label: ODESSA_CITY.nameUk,
    geo: { lat: ODESSA_CITY.lat, lng: ODESSA_CITY.lng },
    metadata: { twin: "odessa" },
  });
}

export function entityFromManifestAsset(
  manifest: OdessaManifest,
  tileId: string,
  asset: { id: string; entityRef?: string; label?: string; layer: string },
): CityEntity | undefined {
  if (asset.entityRef) {
    const building = CITY_BUILDINGS.find((b) => b.id === asset.entityRef);
    if (building) {
      return {
        id: `city_building_${building.id}`,
        kind: "building",
        label: building.label,
        geo: planeToGeo(building.x + building.w / 2, building.y + building.h / 2),
        platformRef: {
          module: "enterprise-city",
          entityId: building.id,
          route: building.route,
          buildingId: building.id,
        },
        tileId,
        layerId: asset.layer,
        metadata: { assetId: asset.id },
      };
    }
  }
  return {
    id: `asset_${asset.id}`,
    kind: "tile",
    label: asset.label || asset.id,
    tileId,
    layerId: asset.layer,
    metadata: { manifestCity: manifest.cityId },
  };
}

export function resolvePlatformRoute(entity: CityEntity | undefined): string | undefined {
  return entity?.platformRef?.route;
}
