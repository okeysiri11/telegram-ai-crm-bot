/**
 * Enterprise City Graphics Engine — Scene Graph.
 * Sprint CG-2. Presentation hierarchy only: City → District → Building → Floor → Room →
 * Interactive Object. This module never mutates `CityBuilding` / `CityDistrictMeta` data — it only
 * reads the real catalogs (`cityCatalog.ts`, `cityDistricts.ts`) and shapes them into a render-
 * friendly tree. No duplicated rendering logic: exactly one function builds the tree, exactly one
 * function walks it.
 *
 * Floor / Room / Interactive Object levels are real, typed extension points, not fabricated data —
 * no per-building floor/room model exists in the platform yet (`ENTERPRISE_CITY_BIBLE.md` §10,
 * "Departments," is still vision), so this module accepts them as optional input rather than
 * inventing any. City → District → Building is real today; Floor → Room → Interactive Object
 * activates automatically the moment real data is passed in, with zero changes to this file.
 */

import { CITY_BUILDINGS, type CityBuilding, type CityBuildingId } from "../cityCatalog";
import { CITY_DISTRICTS, type CityDistrictMeta } from "../cityDistricts";
import type { SceneNode } from "./types";

export type SceneRoomExtension = { id: string; label: string; interactiveObjects?: { id: string; label: string }[] };
export type SceneFloorExtension = { id: string; label: string; rooms?: SceneRoomExtension[] };
export type SceneBuildingExtension = { buildingId: CityBuildingId; floors: SceneFloorExtension[] };

function interactiveObjectNode(buildingId: string, floorId: string, roomId: string, obj: { id: string; label: string }): SceneNode {
  return {
    id: `object:${buildingId}:${floorId}:${roomId}:${obj.id}`,
    kind: "interactive_object",
    refId: obj.id,
    label: obj.label,
    children: [],
  };
}

function roomNode(buildingId: string, floorId: string, room: SceneRoomExtension): SceneNode {
  return {
    id: `room:${buildingId}:${floorId}:${room.id}`,
    kind: "room",
    refId: room.id,
    label: room.label,
    children: (room.interactiveObjects ?? []).map((obj) => interactiveObjectNode(buildingId, floorId, room.id, obj)),
  };
}

function floorNode(buildingId: string, floor: SceneFloorExtension): SceneNode {
  return {
    id: `floor:${buildingId}:${floor.id}`,
    kind: "floor",
    refId: floor.id,
    label: floor.label,
    children: (floor.rooms ?? []).map((room) => roomNode(buildingId, floor.id, room)),
  };
}

function buildingNode(building: CityBuilding, floors?: SceneFloorExtension[]): SceneNode {
  return {
    id: `building:${building.id}`,
    kind: "building",
    refId: building.id,
    label: building.label,
    children: (floors ?? []).map((floor) => floorNode(building.id, floor)),
  };
}

function districtNode(district: CityDistrictMeta, floorsByBuilding: Map<CityBuildingId, SceneFloorExtension[]>): SceneNode {
  const buildings = CITY_BUILDINGS.filter((b) => b.district === district.id && b.kind !== "plaza");
  return {
    id: `district:${district.id}`,
    kind: "district",
    refId: district.id,
    label: district.label,
    children: buildings.map((b) => buildingNode(b, floorsByBuilding.get(b.id))),
  };
}

/**
 * Build the full City scene graph from the real, live catalogs. `floorExtensions` is optional
 * per-building Floor/Room/Interactive-Object detail — omit it entirely today; pass it once real
 * department/floor data exists, with no change required here.
 */
export function buildSceneGraph(floorExtensions: SceneBuildingExtension[] = []): SceneNode {
  const floorsByBuilding = new Map(floorExtensions.map((f) => [f.buildingId, f.floors]));
  return {
    id: "city:root",
    kind: "city",
    label: "Enterprise City",
    children: CITY_DISTRICTS.map((d) => districtNode(d, floorsByBuilding)),
  };
}

/** Depth-first walk — the single traversal every render layer / debug overlay should share. */
export function walkSceneGraph(root: SceneNode, visit: (node: SceneNode, depth: number) => void, depth = 0): void {
  visit(root, depth);
  for (const child of root.children) walkSceneGraph(child, visit, depth + 1);
}

/** Find a node by its stable id (e.g. `"building:crm"`) without a manual walk at every call site. */
export function findSceneNode(root: SceneNode, id: string): SceneNode | null {
  if (root.id === id) return root;
  for (const child of root.children) {
    const hit = findSceneNode(child, id);
    if (hit) return hit;
  }
  return null;
}

/** Node counts per kind — feeds the Debug layer and the performance-budget checks in graphicsConfig. */
export function sceneGraphStats(root: SceneNode): Record<SceneNode["kind"], number> {
  const stats = { city: 0, district: 0, building: 0, floor: 0, room: 0, interactive_object: 0 };
  walkSceneGraph(root, (node) => {
    stats[node.kind] += 1;
  });
  return stats;
}
