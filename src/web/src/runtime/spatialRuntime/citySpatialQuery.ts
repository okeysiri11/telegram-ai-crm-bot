/**
 * City Spatial Query API — Sprint 29.4.
 * Aggregates Spatial · Life · Assets · Citizens · EBN (no rendering).
 */

import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import type { CitySpatialQuery, SpatialEntity } from "./spatialTypes";
import { spatialRegistry } from "./spatialRegistry";
import { locationEngine } from "./locationEngine";
import { routingEngine } from "./routingEngine";

function cityBuildingKey(entity: SpatialEntity): string {
  return entity.cityBuildingId || entity.id;
}

export function buildCitySpatialQuery(): CitySpatialQuery {
  const districts = spatialRegistry.list("district");
  const buildings = spatialRegistry.list("building");

  const buildingsByDistrict: Record<string, SpatialEntity[]> = {};
  for (const d of districts) {
    const key = d.cityDistrictId || d.id;
    buildingsByDistrict[key] = buildings.filter(
      (b) => b.parentId === d.id || b.cityDistrictId === d.cityDistrictId,
    );
  }

  const companiesByBuilding: Record<string, string[]> = {};
  // EBN profiles tagged with cityBuilding
  for (const p of businessNetworkEngine.listProfiles()) {
    const buildingId = String(p.metadata?.cityBuilding || "");
    if (buildingId) {
      (companiesByBuilding[buildingId] ||= []).push(p.id);
    }
  }
  // Asset ownership companies per building
  for (const [buildingId, assets] of Object.entries(assetRuntime.cityQuery().byBuilding)) {
    for (const a of assets) {
      const companyId = a.ownership.companyId || a.assignedCompanyId;
      if (!companyId) continue;
      const list = (companiesByBuilding[buildingId] ||= []);
      if (!list.includes(companyId)) list.push(companyId);
    }
  }
  // Seeded HQ default
  if (!companiesByBuilding.hub?.length) {
    companiesByBuilding.hub = [EBN_HOME_PROFILE_ID];
  }

  const citizensByLocation: Record<string, string[]> = {};
  for (const c of digitalCitizenEngine.listCitizens()) {
    const buildingId = c.presence.cityBuildingId;
    if (buildingId) (citizensByLocation[buildingId] ||= []).push(c.id);
  }
  for (const a of locationEngine.list().filter((x) => x.subjectKind === "citizen" && x.kind === "current")) {
    const ent = spatialRegistry.get(a.entityId);
    const loc = ent?.cityBuildingId || a.entityId;
    const list = (citizensByLocation[loc] ||= []);
    if (!list.includes(a.subjectId)) list.push(a.subjectId);
  }

  const assetsByBuilding: Record<string, string[]> = {};
  for (const [buildingId, assets] of Object.entries(assetRuntime.cityQuery().byBuilding)) {
    assetsByBuilding[buildingId] = assets.map((a) => a.id);
  }

  const projectsByArea: Record<string, string[]> = {};
  const city = lifeEngine.cityRuntime();
  for (const p of city.projects) {
    // Map project members' buildings → area
    const members = lifeEngine.projects.list(p.projectId);
    for (const m of members) {
      const citizen = digitalCitizenEngine.getCitizen(m.citizenId);
      const area = citizen?.presence.cityBuildingId || "hub";
      const list = (projectsByArea[area] ||= []);
      if (!list.includes(p.projectId)) list.push(p.projectId);
    }
    if (!members.length) {
      (projectsByArea.hub ||= []).push(p.projectId);
    }
  }

  const meetingsByOffice: Record<string, string[]> = {};
  for (const m of lifeEngine.meetings.list()) {
    const office = m.buildingId || "hub";
    (meetingsByOffice[office] ||= []).push(m.id);
  }

  return {
    buildingsByDistrict,
    companiesByBuilding,
    citizensByLocation,
    assetsByBuilding,
    projectsByArea,
    meetingsByOffice,
    districts,
    stats: {
      entities: spatialRegistry.list().length,
      buildings: buildings.length,
      districts: districts.length,
      routesCached: routingEngine.cachedCount(),
      assignments: locationEngine.list().length,
    },
  };
}

export function buildingsInDistrict(districtId: string): SpatialEntity[] {
  const d =
    spatialRegistry.list("district").find((x) => x.cityDistrictId === districtId || x.id === districtId) ||
    spatialRegistry.get(districtId.startsWith("spd_") ? districtId : `spd_${districtId}`);
  if (!d) return [];
  return spatialRegistry.children(d.id).filter((e) => e.kind === "building");
}

export function resolveSpatialBuildingId(cityBuildingId: string): string {
  return spatialRegistry.list("building").find((b) => b.cityBuildingId === cityBuildingId)?.id || `spb_${cityBuildingId}`;
}

export { cityBuildingKey };
