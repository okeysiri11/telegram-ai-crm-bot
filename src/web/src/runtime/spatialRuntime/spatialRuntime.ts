/**
 * Enterprise Spatial Runtime Engine — Sprint 29.4.
 * Odessa Digital Twin foundation (runtime only).
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import {
  SPATIAL_RUNTIME_VERSION,
  ODESSA_CITY,
  type LocationAssignmentKind,
  type SpatialDistrictKind,
  type SpatialRoute,
} from "./spatialTypes";
import { spatialRegistry } from "./spatialRegistry";
import { locationEngine } from "./locationEngine";
import { routingEngine } from "./routingEngine";
import { spatialEvents, publishSpatialEvent } from "./spatialEvents";
import { spatialPermissions } from "./spatialPermissions";
import { seedOdessaSpatial } from "./spatialSeed";
import {
  buildCitySpatialQuery,
  buildingsInDistrict,
  resolveSpatialBuildingId,
} from "./citySpatialQuery";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "spatial_open",
    action: "open_spatial_runtime",
    label: "Open Spatial Runtime",
    kind: "navigate",
    keywords: ["spatial", "odessa", "district", "location", "route"],
    route: "/spatial",
    permission: "*",
  });
  commandRuntime.register({
    id: "spatial_route",
    action: "spatial_route",
    label: "Route between buildings",
    kind: "system",
    keywords: ["route", "navigate", "path"],
    permission: "*",
    handler: async (_ctx, args) => {
      const from = resolveSpatialBuildingId(String(args.from || "hub"));
      const to = resolveSpatialBuildingId(String(args.to || "developer"));
      const route = spatialRuntime.route(from, to);
      return {
        ok: !!route,
        message: route ? `${Math.round(route.distanceM)}m · ${route.travelTimeSec}s` : "no_route",
      };
    },
  });
}

function syncCitizenLocations() {
  for (const c of digitalCitizenEngine.listCitizens()) {
    const buildingId = c.presence.cityBuildingId;
    if (!buildingId) continue;
    const entityId = resolveSpatialBuildingId(buildingId);
    if (!spatialRegistry.get(entityId)) continue;
    locationEngine.assign({
      subjectKind: "citizen",
      subjectId: c.id,
      kind: "current",
      entityId,
    });
    locationEngine.assign({
      subjectKind: "citizen",
      subjectId: c.id,
      kind: "company_office",
      entityId: resolveSpatialBuildingId("hub"),
    });
    if (c.presence.locationLabel === "Remote") {
      locationEngine.assign({
        subjectKind: "citizen",
        subjectId: c.id,
        kind: "remote_workplace",
        entityId: "spv_remote",
      });
    }
  }
}

export const spatialRuntime = {
  version: SPATIAL_RUNTIME_VERSION,
  odessa: ODESSA_CITY,

  startup() {
    if (booted) {
      return this.stats();
    }
    commandRuntime.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    lifeEngine.startup();
    assetRuntime.startup();
    seedOdessaSpatial();
    syncCitizenLocations();
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "spatial_runtime", ready: true, version: SPATIAL_RUNTIME_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  /** Entity registry */
  get(id: string) {
    if (!booted) this.startup();
    return spatialRegistry.get(id);
  },

  list(kind?: Parameters<typeof spatialRegistry.list>[0]) {
    if (!booted) this.startup();
    return spatialRegistry.list(kind);
  },

  children(parentId: string) {
    if (!booted) this.startup();
    return spatialRegistry.children(parentId);
  },

  ancestors(entityId: string) {
    if (!booted) this.startup();
    return spatialRegistry.ancestors(entityId);
  },

  hierarchy() {
    if (!booted) this.startup();
    return {
      country: this.list("country"),
      region: this.list("region"),
      city: this.list("city"),
      district: this.list("district"),
      street: this.list("street"),
      building: this.list("building"),
      floor: this.list("floor"),
      room: this.list("room"),
      workspace: this.list("workspace"),
      virtual_space: this.list("virtual_space"),
      poi: this.list("poi"),
      zone: this.list("zone"),
    };
  },

  /** District runtime */
  districts(kind?: SpatialDistrictKind) {
    if (!booted) this.startup();
    const all = this.list("district");
    return kind ? all.filter((d) => d.districtKind === kind) : all;
  },

  buildingsByDistrict(districtId: string) {
    if (!booted) this.startup();
    return buildingsInDistrict(districtId);
  },

  /** Location engine */
  assignLocation(input: {
    subjectKind: "citizen" | "asset" | "company" | "meeting" | "project";
    subjectId: string;
    kind: LocationAssignmentKind;
    entityId: string;
    dynamic?: { lat: number; lng: number; x?: number; y?: number };
  }) {
    if (!booted) this.startup();
    return locationEngine.assign(input);
  },

  currentLocation(subjectKind: "citizen" | "asset" | "company" | "meeting" | "project", subjectId: string) {
    if (!booted) this.startup();
    return locationEngine.getCurrent(subjectKind, subjectId);
  },

  locationsFor(subjectKind: "citizen" | "asset" | "company" | "meeting" | "project", subjectId: string) {
    if (!booted) this.startup();
    return locationEngine.forSubject(subjectKind, subjectId);
  },

  setDynamicPosition(
    subjectKind: "citizen" | "asset" | "company" | "meeting" | "project",
    subjectId: string,
    geo: { lat: number; lng: number; x?: number; y?: number },
    nearEntityId?: string,
  ) {
    if (!booted) this.startup();
    return locationEngine.setDynamicPosition(subjectKind, subjectId, geo, nearEntityId);
  },

  /** Routing */
  route(fromEntityId: string, toEntityId: string, mode: SpatialRoute["mode"] = "walk") {
    if (!booted) this.startup();
    return routingEngine.route(fromEntityId, toEntityId, mode);
  },

  distance(fromEntityId: string, toEntityId: string) {
    if (!booted) this.startup();
    return routingEngine.distance(fromEntityId, toEntityId);
  },

  travelTime(fromEntityId: string, toEntityId: string, mode: SpatialRoute["mode"] = "walk") {
    if (!booted) this.startup();
    return routingEngine.travelTime(fromEntityId, toEntityId, mode);
  },

  navigationNodes() {
    if (!booted) this.startup();
    return routingEngine.listNodes();
  },

  /** Move asset + spatial event */
  moveAsset(
    assetId: string,
    location: Parameters<typeof assetRuntime.move>[1],
  ) {
    if (!booted) this.startup();
    const moved = assetRuntime.move(assetId, location);
    if (moved) {
      const entityId = location.buildingId
        ? resolveSpatialBuildingId(location.buildingId)
        : undefined;
      publishSpatialEvent("MovedAsset", {
        subjectId: assetId,
        entityId,
        buildingId: location.buildingId,
      });
      if (entityId) {
        locationEngine.assign({
          subjectKind: "asset",
          subjectId: assetId,
          kind: "current",
          entityId,
        });
      }
    }
    return moved;
  },

  cityQuery() {
    if (!booted) this.startup();
    return buildCitySpatialQuery();
  },

  relations: {
    list: (entityId?: string, kind?: Parameters<typeof spatialRegistry.relations>[1]) => {
      if (!booted) spatialRuntime.startup();
      return spatialRegistry.relations(entityId, kind);
    },
    contains: (a: string, b: string) => {
      if (!booted) spatialRuntime.startup();
      return spatialRegistry.contains(a, b);
    },
    adjacent: (a: string, b: string) => {
      if (!booted) spatialRuntime.startup();
      return spatialRegistry.adjacent(a, b);
    },
    connected: (a: string, b: string) => {
      if (!booted) spatialRuntime.startup();
      return spatialRegistry.connected(a, b);
    },
  },

  permissions: spatialPermissions,
  events: spatialEvents,

  stats() {
    if (!booted) this.startup();
    return {
      version: SPATIAL_RUNTIME_VERSION,
      city: ODESSA_CITY.name,
      entities: spatialRegistry.list().length,
      buildings: spatialRegistry.list("building").length,
      districts: spatialRegistry.list("district").length,
      assignments: locationEngine.list().length,
      navNodes: routingEngine.listNodes().length,
      routesCached: routingEngine.cachedCount(),
      events: spatialEvents.list(200).length,
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    return {
      version: SPATIAL_RUNTIME_VERSION,
      odessa: ODESSA_CITY,
      hierarchy: this.hierarchy(),
      districts: this.districts(),
      assignments: locationEngine.list(),
      events: spatialEvents.list(30),
      city: this.cityQuery(),
      stats: this.stats(),
      sampleRoute: this.route(
        resolveSpatialBuildingId("hub"),
        resolveSpatialBuildingId("developer"),
      ),
    };
  },

  __resetForTests() {
    spatialRegistry.clear();
    locationEngine.clear();
    routingEngine.clear();
    spatialEvents.clear();
    booted = false;
  },
};
