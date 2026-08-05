/**
 * Runtime data provider — Sprint 29.5.
 * Aggregates live Spatial · Life · Citizens · EBN · Assets · Workflow (no mocks).
 */

import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { spatialRuntime, ODESSA_CITY } from "@/runtime/spatialRuntime";
import { lifeEngine } from "@/runtime/lifeEngine";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import type {
  ActivityVisualState,
  AssetVisualState,
  BuildingOpenState,
  BuildingVisualState,
  BuildingVisualStatus,
  CitizenVisualState,
  CompanyVisualState,
  DistrictVisualState,
} from "./cityVisualizationTypes";

function now() {
  return new Date().toISOString();
}

function toneToStatus(tone: string): BuildingVisualStatus {
  switch (tone) {
    case "busy":
      return "busy";
    case "alert":
      return "alert";
    case "active":
      return "active";
    case "offline":
      return "offline";
    default:
      return "idle";
  }
}

function openStateFromPresence(occupancy: number, meetingCount: number): BuildingOpenState {
  if (meetingCount > 0 || occupancy > 0) return "open";
  return "open"; // enterprise buildings default open during runtime; closed reserved for future hours
}

const EQUIPMENT_TYPES = new Set(["machine", "server", "computer", "construction_equipment"]);
const CONSTRUCTION_TYPES = new Set(["construction_equipment"]);

export const runtimeDataProvider = {
  ensureDeps() {
    spatialRuntime.startup();
    lifeEngine.startup();
    digitalCitizenEngine.startup();
    businessNetworkEngine.startup();
    assetRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
  },

  cityMeta() {
    return { cityId: ODESSA_CITY.id, cityName: ODESSA_CITY.name };
  },

  buildings(): BuildingVisualState[] {
    this.ensureDeps();
    const spatialQ = spatialRuntime.cityQuery();
    const life = lifeEngine.cityRuntime();
    const assetQ = assetRuntime.cityQuery();
    const occupancyByBuilding = new Map(
      life.occupancy.map((o) => [o.buildingId, o] as const),
    );
    const meetings = life.meetings;
    const projectsByArea = spatialQ.projectsByArea;
    const companiesByBuilding = spatialQ.companiesByBuilding;

    return CITY_BUILDINGS.map((b) => {
      const spatial = spatialRuntime.list("building").find((e) => e.cityBuildingId === b.id);
      const occ = occupancyByBuilding.get(b.id);
      const occupancy = occ?.occupants.length || spatialQ.citizensByLocation[b.id]?.length || 0;
      const buildingMeetings = meetings.filter((m) => m.buildingId === b.id);
      const meetingCount = buildingMeetings.filter((m) => m.status === "active").length;
      const assets = assetQ.byBuilding[b.id] || [];
      const maint = assets.filter((a) => a.status === "maintenance").length;
      let status: BuildingVisualStatus = "idle";
      if (maint > 0) status = "maintenance";
      else if (meetingCount > 0 || occupancy > 6) status = "busy";
      else if (occupancy > 0 || assets.length > 0) status = "active";
      if (occ) status = toneToStatus(occupancy > 6 || meetingCount > 0 ? "busy" : occupancy > 0 ? "active" : "idle");
      if (maint > 0) status = "alert";

      return {
        buildingId: b.id,
        spatialEntityId: spatial?.id,
        districtId: b.district,
        status,
        occupancy,
        businessActivity: Math.min(
          100,
          occupancy * 12 + meetingCount * 20 + (companiesByBuilding[b.id]?.length || 0) * 15,
        ),
        openState: openStateFromPresence(occupancy, meetingCount),
        meetingCount,
        meetingIds: buildingMeetings.map((m) => m.id),
        projectIds: projectsByArea[b.id] || [],
        companyIds: companiesByBuilding[b.id] || [],
        assetCount: assets.length,
        processLabel: occ?.activityLabel,
        branding: {
          labelOverride: b.label,
          accentHint: b.district,
        },
        updatedAt: now(),
      };
    });
  },

  districts(): DistrictVisualState[] {
    this.ensureDeps();
    const buildings = this.buildings();
    const spatialDistricts = spatialRuntime.list("district");
    const byDistrict = new Map<string, BuildingVisualState[]>();
    for (const b of buildings) {
      if (!b.districtId) continue;
      (byDistrict.get(b.districtId) || byDistrict.set(b.districtId, []).get(b.districtId)!).push(b);
    }

    return spatialDistricts.map((d) => {
      const districtId = d.cityDistrictId || d.id;
      const list = byDistrict.get(districtId) || buildings.filter((b) => b.districtId === districtId);
      const population = list.reduce((s, b) => s + b.occupancy, 0);
      const companies = new Set(list.flatMap((b) => b.companyIds));
      const construction =
        d.districtKind === "construction"
          ? Math.min(100, list.reduce((s, b) => s + b.assetCount, 0) * 10)
          : list.some((b) => b.status === "maintenance")
            ? 25
            : 0;
      const traffic = Math.min(100, population * 8 + list.reduce((s, b) => s + b.meetingCount, 0) * 10);
      const economic = Math.min(
        100,
        companies.size * 18 + list.reduce((s, b) => s + b.businessActivity, 0) / Math.max(1, list.length),
      );
      const activity = Math.min(100, Math.round((population * 10 + economic + traffic) / 3));
      let runtimeStatus: BuildingVisualStatus = "idle";
      if (list.some((b) => b.status === "alert" || b.status === "maintenance")) runtimeStatus = "alert";
      else if (list.some((b) => b.status === "busy")) runtimeStatus = "busy";
      else if (list.some((b) => b.status === "active") || population > 0) runtimeStatus = "active";

      return {
        districtId,
        spatialEntityId: d.id,
        districtKind: d.districtKind,
        activity,
        population,
        businessDensity: Math.min(100, companies.size * 20 + list.length * 5),
        constructionActivity: construction,
        trafficDensity: traffic,
        economicActivity: Math.round(economic),
        runtimeStatus,
        buildingIds: list.map((b) => b.buildingId),
        updatedAt: now(),
      };
    });
  },

  citizens(): CitizenVisualState[] {
    this.ensureDeps();
    return digitalCitizenEngine.listCitizens().map((c) => {
      const memberships = digitalCitizenEngine.listMemberships(c.id);
      const primary = memberships[0];
      const remote =
        c.presence.locationLabel === "Remote" ||
        c.presence.status === "vacation" ||
        !c.presence.cityBuildingId;
      const workspaceId = spatialRuntime
        .locationsFor("citizen", c.id)
        .find((a) => a.kind === "assigned")?.entityId;

      return {
        citizenId: c.id,
        displayName: c.displayName,
        buildingId: c.presence.cityBuildingId,
        workspaceId,
        companyId: primary?.orgId || EBN_HOME_PROFILE_ID,
        presence: c.presence.status,
        role: primary?.role,
        activity: c.presence.locationLabel || c.presence.status,
        remote,
        avatarRef: c.avatarUrl || `avatar://${c.id}`,
        updatedAt: now(),
      };
    });
  },

  companies(): CompanyVisualState[] {
    this.ensureDeps();
    const spatialQ = spatialRuntime.cityQuery();
    const buildingByCompany = new Map<string, string[]>();
    for (const [buildingId, companies] of Object.entries(spatialQ.companiesByBuilding)) {
      for (const companyId of companies) {
        const list = buildingByCompany.get(companyId) || [];
        if (!list.includes(buildingId)) list.push(buildingId);
        buildingByCompany.set(companyId, list);
      }
    }
    return businessNetworkEngine.listProfiles().map((p) => ({
      companyId: p.id,
      name: p.companyName,
      buildingIds: buildingByCompany.get(p.id) || (p.metadata?.cityBuilding ? [String(p.metadata.cityBuilding)] : []),
      category: String(p.category || ""),
      relationshipCount: businessNetworkEngine.listRelationships(p.id).length,
      updatedAt: now(),
    }));
  },

  assets(): AssetVisualState[] {
    this.ensureDeps();
    return assetRuntime.list().map((a) => {
      const type = a.type;
      return {
        assetId: a.id,
        name: a.profile.name,
        type,
        category: a.category,
        buildingId: a.location.buildingId,
        districtId: a.location.districtId,
        status: a.status,
        available: a.available,
        isVehicle: type === "vehicle",
        isEquipment: EQUIPMENT_TYPES.has(type),
        isWarehouse: type === "warehouse",
        isHeadquarters: type === "headquarters",
        isConstruction: CONSTRUCTION_TYPES.has(type) || type === "construction_equipment",
        isDrone: type === "drone",
        updatedAt: now(),
      };
    });
  },

  activities(): ActivityVisualState[] {
    this.ensureDeps();
    const out: ActivityVisualState[] = [];
    for (const m of lifeEngine.meetings.list()) {
      out.push({
        id: `act_mtg_${m.id}`,
        kind: "meeting",
        label: m.title,
        buildingId: m.buildingId,
        subjectIds: m.attendeeIds,
        status: m.status,
        at: m.createdAt,
      });
    }
    for (const mv of lifeEngine.movements.list().slice(0, 30)) {
      const actor = mv.actorCitizenId || mv.actorAiId || "unknown";
      out.push({
        id: `act_mv_${mv.id}`,
        kind: "movement",
        label: `Move ${actor}`,
        buildingId: mv.toBuildingId || mv.fromBuildingId,
        subjectIds: mv.actorCitizenId ? [mv.actorCitizenId] : [],
        status: mv.status,
        at: mv.arrivedAt || mv.startedAt,
      });
    }
    for (const p of lifeEngine.cityRuntime().projects) {
      out.push({
        id: `act_proj_${p.projectId}`,
        kind: "project",
        label: p.projectName,
        buildingId: "hub",
        subjectIds: [],
        status: p.status,
        at: now(),
      });
    }
    for (const h of workflowRuntime.history(20)) {
      out.push({
        id: `act_wf_${h.id}`,
        kind: "workflow",
        label: h.name || h.definitionId,
        subjectIds: [],
        status: h.status,
        at: h.completedAt || h.startedAt,
      });
    }
    for (const h of automationEngine.history(15)) {
      out.push({
        id: `act_auto_${h.id}`,
        kind: "automation",
        label: h.automationId,
        subjectIds: [],
        status: h.status,
        at: h.at,
      });
    }
    return out.sort((a, b) => b.at.localeCompare(a.at));
  },
};
