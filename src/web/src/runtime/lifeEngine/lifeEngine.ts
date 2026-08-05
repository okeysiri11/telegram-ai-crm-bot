/**
 * Enterprise Life Engine — Sprint 29.2.
 * Orchestrates Citizens · EBN · City · AI · Workflow · Automation into live activity.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER, EDC_CITIZEN_DEV, EDC_ORG_DEMO } from "@/runtime/digitalCitizen";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID } from "@/runtime/businessNetwork";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { LIFE_ENGINE_VERSION } from "./lifeTypes";
import type { LifePresence, MovementKind, CityRuntimeSnapshot } from "./lifeTypes";
import { lifeEventEngine, publishLifeEvent } from "./lifeEventEngine";
import { activityTimeline } from "./activityTimeline";
import { buildingOccupancy } from "./buildingOccupancy";
import { cityMovement } from "./cityMovement";
import { livePresence, toCitizenPresence, toLifePresence } from "./livePresence";
import { businessInteractions } from "./businessInteractions";
import { projectParticipation } from "./projectParticipation";
import { lifeMeetings, lifeVehicles } from "./lifeMeetings";

let booted = false;
let busUnsub: (() => void) | null = null;

function syncOccupancyFromCitizens() {
  for (const c of digitalCitizenEngine.listCitizens()) {
    const buildingId = c.presence.cityBuildingId;
    if (!buildingId) continue;
    const life = toLifePresence(c.presence.status);
    if (life === "offline" || life === "vacation") {
      buildingOccupancy.leave(c.id);
      continue;
    }
    buildingOccupancy.enter({
      buildingId,
      citizenId: c.id,
      kind: "employee",
    });
  }
}

function seedLife() {
  if (lifeVehicles.list().length) return;

  lifeVehicles.register("Fleet Van 1", "veh_van_1");
  lifeVehicles.register("Courier Bike", "veh_bike_1");

  projectParticipation.startProject("proj_platform", "ADOS Platform", EDC_CITIZEN_OWNER);
  projectParticipation.join({
    projectId: "proj_platform",
    projectName: "ADOS Platform",
    citizenId: EDC_CITIZEN_DEV,
    role: "contributor",
  });
  projectParticipation.assign("proj_platform", EDC_CITIZEN_DEV, "Implement Life Engine bridge");

  syncOccupancyFromCitizens();

  for (const a of digitalCitizenEngine.listAi()) {
    if (a.active && a.assignedCitizenId) {
      publishLifeEvent("ai_activated", {
        aiId: a.id,
        citizenId: a.assignedCitizenId,
        payload: { name: a.name, kind: a.kind },
      });
      const citizen = digitalCitizenEngine.getCitizen(a.assignedCitizenId);
      if (citizen?.presence.cityBuildingId) {
        buildingOccupancy.enter({
          buildingId: citizen.presence.cityBuildingId,
          aiId: a.id,
          kind: "ai",
        });
      }
    }
  }

  publishLifeEvent("citizen_starts_work", {
    citizenId: EDC_CITIZEN_OWNER,
    buildingId: "hub",
    companyId: EBN_HOME_PROFILE_ID,
    message: "Workday open",
  });
}

function attachPlatformBridges() {
  busUnsub?.();
  busUnsub = enterpriseEventBus.subscribe((event) => {
    if (event.type === "workflow_update") {
      const status = String(event.payload?.status || "");
      const definitionId = String(event.payload?.definitionId || event.payload?.workflowId || "");
      if (status === "completed" || status === "running") {
        publishLifeEvent(status === "completed" ? "workflow_completed" : "workflow_executed", {
          workflowId: definitionId || String(event.payload?.sessionId || ""),
          payload: { ...event.payload },
        });
      }
    }
    if (event.type === "digital_citizen_update") {
      const name = String(event.payload?.event || "");
      const citizenId = String(event.payload?.citizenId || "");
      if (name === "PresenceChanged" && citizenId) {
        const c = digitalCitizenEngine.getCitizen(citizenId);
        if (c?.presence.cityBuildingId) {
          const life = toLifePresence(c.presence.status);
          if (life === "offline" || life === "vacation") {
            buildingOccupancy.leave(citizenId);
            publishLifeEvent("citizen_leaves_office", {
              citizenId,
              buildingId: c.presence.cityBuildingId,
            });
          } else {
            buildingOccupancy.enter({
              buildingId: c.presence.cityBuildingId,
              citizenId,
              kind: "employee",
            });
            if (life === "working" || life === "available") {
              publishLifeEvent("citizen_enters_office", {
                citizenId,
                buildingId: c.presence.cityBuildingId,
                companyId: c.primaryOrgId,
              });
            }
          }
        }
      }
      if (name === "DocumentSigned") {
        publishLifeEvent("document_signed", {
          citizenId,
          documentRef: String(event.payload?.documentRef || ""),
        });
      }
      if (name === "AIAssigned") {
        publishLifeEvent("ai_activated", {
          citizenId,
          aiId: String(event.payload?.aiId || ""),
        });
      }
    }
    if (event.type === "business_network_update") {
      const name = String(event.payload?.event || "");
      if (name === "DocumentLinked" || name === "PartnerAdded") {
        publishLifeEvent(name === "DocumentLinked" ? "document_shared" : "partnership_discussion", {
          companyId: String(event.payload?.profileId || EBN_HOME_PROFILE_ID),
          payload: { ...event.payload },
        });
      }
    }
  });
}

function registerCommands() {
  commandRuntime.register({
    id: "life_open",
    action: "open_life_engine",
    label: "Open Life Engine",
    kind: "navigate",
    keywords: ["life", "city", "occupancy", "timeline"],
    route: "/life-engine",
    permission: "*",
  });
  commandRuntime.register({
    id: "life_enter_office",
    action: "life_enter_office",
    label: "Citizen Enter Office",
    kind: "system",
    keywords: ["office", "enter", "life"],
    permission: "*",
    handler: async (_ctx, args) => {
      const citizenId = String(args.citizenId || EDC_CITIZEN_OWNER);
      const buildingId = String(args.buildingId || "hub");
      lifeEngine.enterOffice(citizenId, buildingId);
      return { ok: true, message: buildingId };
    },
  });
}

export const lifeEngine = {
  version: LIFE_ENGINE_VERSION,

  startup() {
    if (booted) {
      return {
        version: LIFE_ENGINE_VERSION,
        events: lifeEventEngine.list(400).length,
        online: digitalCitizenEngine.listCitizens().filter((c) => {
          const p = toLifePresence(c.presence.status);
          return p !== "offline" && p !== "vacation";
        }).length,
        activeMeetings: lifeMeetings.active().length,
        inTransit: cityMovement.inTransit().length,
        buildingsTracked: buildingOccupancy.list().length,
        interactions: businessInteractions.list(200).length,
        participants: projectParticipation.list().length,
      };
    }
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    seedLife();
    attachPlatformBridges();
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "life_engine", ready: true, version: LIFE_ENGINE_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  /** Life events */
  record: publishLifeEvent,
  events(limit = 60) {
    this.startup();
    return lifeEventEngine.list(limit);
  },

  timeline: activityTimeline,

  /** Presence */
  setLifePresence(citizenId: string, presence: LifePresence, buildingId?: string) {
    this.startup();
    const status = toCitizenPresence(presence);
    digitalCitizenEngine.setPresence(citizenId, status, {
      cityBuildingId: buildingId,
      locationLabel: presence === "remote" ? "Remote" : presence === "travelling" ? "In transit" : undefined,
    });
    if (presence === "travelling") {
      // occupancy cleared on leave; movement caller handles transit
      buildingOccupancy.leave(citizenId);
    } else if (buildingId && presence !== "offline" && presence !== "vacation") {
      buildingOccupancy.enter({ buildingId, citizenId, kind: presence === "available" ? "visitor" : "employee" });
    }
    return digitalCitizenEngine.getCitizen(citizenId);
  },

  enterOffice(citizenId: string, buildingId: string, companyId?: string) {
    this.startup();
    const prev = digitalCitizenEngine.getCitizen(citizenId)?.presence.cityBuildingId;
    if (prev && prev !== buildingId) buildingOccupancy.leaveBuilding(prev, citizenId);
    this.setLifePresence(citizenId, "working", buildingId);
    buildingOccupancy.enter({ buildingId, citizenId, kind: "employee" });
    return publishLifeEvent("citizen_enters_office", {
      citizenId,
      buildingId,
      companyId: companyId || EBN_HOME_PROFILE_ID,
    });
  },

  leaveOffice(citizenId: string, buildingId?: string) {
    this.startup();
    const b =
      buildingId || digitalCitizenEngine.getCitizen(citizenId)?.presence.cityBuildingId || "hub";
    buildingOccupancy.leave(citizenId);
    this.setLifePresence(citizenId, "offline");
    return publishLifeEvent("citizen_leaves_office", { citizenId, buildingId: b });
  },

  startWork(citizenId: string, buildingId?: string) {
    this.startup();
    const b = buildingId || digitalCitizenEngine.getCitizen(citizenId)?.presence.cityBuildingId || "hub";
    this.enterOffice(citizenId, b);
    return publishLifeEvent("citizen_starts_work", { citizenId, buildingId: b, companyId: EBN_HOME_PROFILE_ID });
  },

  finishWork(citizenId: string) {
    this.startup();
    const b = digitalCitizenEngine.getCitizen(citizenId)?.presence.cityBuildingId;
    this.leaveOffice(citizenId, b);
    return publishLifeEvent("citizen_finishes_work", { citizenId, buildingId: b });
  },

  /** Movement */
  move(input: {
    kind: MovementKind;
    citizenId?: string;
    aiId?: string;
    vehicleId?: string;
    fromBuildingId?: string;
    toBuildingId?: string;
    purpose?: string;
  }) {
    this.startup();
    if (input.citizenId) this.setLifePresence(input.citizenId, "travelling");
    const move = cityMovement.start({
      kind: input.kind,
      actorCitizenId: input.citizenId,
      actorAiId: input.aiId,
      vehicleId: input.vehicleId,
      fromBuildingId: input.fromBuildingId,
      toBuildingId: input.toBuildingId,
      purpose: input.purpose,
    });
    if (input.vehicleId && input.citizenId) {
      lifeVehicles.assign(input.vehicleId, input.citizenId, input.fromBuildingId, input.toBuildingId);
    }
    return move;
  },

  arrive(movementId: string) {
    this.startup();
    const move = cityMovement.arrive(movementId);
    if (move?.actorCitizenId && move.toBuildingId) {
      const presence: LifePresence = move.kind === "office_to_meeting" ? "in_meeting" : "working";
      this.setLifePresence(move.actorCitizenId, presence, move.toBuildingId);
    }
    if (move?.vehicleId) lifeVehicles.setStatus(move.vehicleId, "arrived", move.toBuildingId);
    return move;
  },

  /** Meetings */
  createMeeting(input: Parameters<typeof lifeMeetings.create>[0]) {
    this.startup();
    return lifeMeetings.create(input);
  },

  startMeeting(meetingId: string) {
    this.startup();
    const m = lifeMeetings.start(meetingId);
    if (m) {
      for (const id of m.attendeeIds) {
        this.setLifePresence(id, "in_meeting", m.buildingId);
      }
    }
    return m;
  },

  endMeeting(meetingId: string) {
    this.startup();
    const m = lifeMeetings.end(meetingId);
    if (m) {
      for (const id of m.attendeeIds) {
        this.setLifePresence(id, "available", m.buildingId);
      }
    }
    return m;
  },

  /** Business */
  businessVisit(fromCitizenId: string, companyId: string, buildingId: string, partnerCompanyId?: string) {
    this.startup();
    this.enterOffice(fromCitizenId, buildingId, companyId);
    return businessInteractions.record("business_visit", {
      fromCitizenId,
      companyId,
      partnerCompanyId,
      buildingId,
      detail: "Business visit",
    });
  },

  inviteMeeting(fromCitizenId: string, toCitizenId: string, buildingId?: string) {
    this.startup();
    return businessInteractions.record("meeting_invitation", {
      fromCitizenId,
      toCitizenId,
      buildingId,
      detail: "Meeting invitation",
    });
  },

  exchangeDocument(fromCitizenId: string, documentRef: string, companyId?: string) {
    this.startup();
    digitalCitizenEngine.signDocument(fromCitizenId, documentRef);
    businessInteractions.record("document_exchange", {
      fromCitizenId,
      documentRef,
      companyId,
      detail: documentRef,
    });
    return publishLifeEvent("document_signed", { citizenId: fromCitizenId, documentRef, companyId });
  },

  /** Projects */
  projects: projectParticipation,

  /** Occupancy */
  occupancy(buildingId?: string) {
    if (!booted) this.startup();
    if (buildingId) return [buildingOccupancy.snapshot(buildingId)];
    return buildingOccupancy.allSnapshots(CITY_BUILDINGS.map((b) => b.id));
  },

  /** City Runtime API */
  cityRuntime(): CityRuntimeSnapshot {
    if (!booted) this.startup();
    const citizens = digitalCitizenEngine.listCitizens().map((c) => {
      let presence = toLifePresence(c.presence.status);
      if (c.presence.locationLabel === "In transit") presence = "travelling";
      if (c.presence.locationLabel === "Remote") presence = "remote";
      return {
        id: c.id,
        displayName: c.displayName,
        presence,
        buildingId: c.presence.cityBuildingId,
      };
    });
    const projects = [...new Map(projectParticipation.list().map((p) => [p.projectId, p])).values()].map(
      (p) => ({
        projectId: p.projectId,
        projectName: p.projectName,
        memberCount: projectParticipation.list(p.projectId).length,
        status: "active",
      }),
    );
    const ai = digitalCitizenEngine.listAi().map((a) => ({
      id: a.id,
      name: a.name,
      kind: a.kind,
      assignedCitizenId: a.assignedCitizenId,
      active: a.active,
    }));
    return {
      version: LIFE_ENGINE_VERSION,
      citizens,
      occupancy: this.occupancy(),
      meetings: lifeMeetings.list(),
      vehicles: lifeVehicles.list(),
      activities: lifeEventEngine.list(40),
      ai,
      projects,
      movements: cityMovement.list().slice(0, 20),
      stats: {
        events: lifeEventEngine.list(400).length,
        online: citizens.filter((c) => !["offline", "vacation"].includes(c.presence)).length,
        activeMeetings: lifeMeetings.active().length,
        inTransit: cityMovement.inTransit().length,
      },
    };
  },

  stats() {
    if (!booted) this.startup();
    const citizens = digitalCitizenEngine.listCitizens();
    const online = citizens.filter((c) => {
      const p = toLifePresence(c.presence.status);
      return p !== "offline" && p !== "vacation";
    }).length;
    return {
      version: LIFE_ENGINE_VERSION,
      events: lifeEventEngine.list(400).length,
      online,
      activeMeetings: lifeMeetings.active().length,
      inTransit: cityMovement.inTransit().length,
      buildingsTracked: new Set(buildingOccupancy.list().map((o) => o.buildingId)).size,
      interactions: businessInteractions.list(200).length,
      participants: projectParticipation.list().length,
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    return {
      version: LIFE_ENGINE_VERSION,
      city: this.cityRuntime(),
      timeline: activityTimeline.unified(40),
      interactions: businessInteractions.list(20),
      participation: projectParticipation.list(),
      stats: this.stats(),
      org: EDC_ORG_DEMO,
      partner: EBN_PARTNER_PROFILE_ID,
    };
  },

  livePresence,
  vehicles: lifeVehicles,
  meetings: lifeMeetings,
  movements: cityMovement,
  interactions: businessInteractions,

  __resetForTests() {
    busUnsub?.();
    busUnsub = null;
    lifeEventEngine.clear();
    buildingOccupancy.clear();
    cityMovement.clear();
    businessInteractions.clear();
    projectParticipation.clear();
    lifeMeetings.clear();
    lifeVehicles.clear();
    booted = false;
  },
};
