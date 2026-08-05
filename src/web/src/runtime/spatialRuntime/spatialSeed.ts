/**
 * Odessa Digital Twin spatial seed — Sprint 29.4.
 * Projects Enterprise City catalog into spatial hierarchy (no rendering).
 */

import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { CITY_DISTRICTS, streetGraph } from "@/enterprise-city/cityDistricts";
import { ODESSA_CITY } from "./spatialTypes";
import { spatialRegistry, planeToGeo, districtKindForCityDistrict } from "./spatialRegistry";
import { publishSpatialEvent } from "./spatialEvents";
import { routingEngine } from "./routingEngine";

export function seedOdessaSpatial() {
  if (spatialRegistry.get(ODESSA_CITY.id)) return;

  spatialRegistry.upsert({
    id: "country_ua",
    kind: "country",
    name: "Ukraine",
    geo: { lat: 48.3794, lng: 31.1656 },
    metadata: { iso: "UA" },
  });

  spatialRegistry.upsert({
    id: "region_odesa",
    kind: "region",
    name: ODESSA_CITY.region,
    parentId: "country_ua",
    geo: { lat: ODESSA_CITY.lat, lng: ODESSA_CITY.lng },
    metadata: {},
  });

  spatialRegistry.upsert({
    id: ODESSA_CITY.id,
    kind: "city",
    name: ODESSA_CITY.name,
    parentId: "region_odesa",
    geo: { lat: ODESSA_CITY.lat, lng: ODESSA_CITY.lng, label: ODESSA_CITY.nameUk },
    metadata: { twin: "odessa", timezone: ODESSA_CITY.timezone },
  });
  spatialRegistry.contains("country_ua", "region_odesa");
  spatialRegistry.contains("region_odesa", ODESSA_CITY.id);

  // Logistics / medical / residential as extended runtime districts (Odessa twin)
  const extraDistricts: {
    id: string;
    name: string;
    kind: ReturnType<typeof districtKindForCityDistrict>;
    x: number;
    y: number;
  }[] = [
    { id: "spd_logistics", name: "Logistics District", kind: "logistics", x: 22, y: 48 },
    { id: "spd_medical", name: "Medical District", kind: "medical", x: 58, y: 38 },
    { id: "spd_residential", name: "Residential District", kind: "residential", x: 80, y: 48 },
  ];

  for (const d of CITY_DISTRICTS) {
    const id = `spd_${d.id}`;
    spatialRegistry.upsert({
      id,
      kind: "district",
      name: d.label,
      parentId: ODESSA_CITY.id,
      cityDistrictId: d.id,
      districtKind: districtKindForCityDistrict(d.id),
      geo: planeToGeo(d.x, d.y),
      region: {
        id: `reg_${d.id}`,
        name: d.label,
        minX: d.x - 12,
        minY: d.y - 12,
        maxX: d.x + 12,
        maxY: d.y + 12,
        center: planeToGeo(d.x, d.y),
      },
      metadata: { labelRu: d.labelRu, css: d.css },
    });
    spatialRegistry.contains(ODESSA_CITY.id, id);
  }

  for (const d of extraDistricts) {
    spatialRegistry.upsert({
      id: d.id,
      kind: "district",
      name: d.name,
      parentId: ODESSA_CITY.id,
      districtKind: d.kind,
      geo: planeToGeo(d.x, d.y),
      region: {
        id: `reg_${d.id}`,
        name: d.name,
        minX: d.x - 10,
        minY: d.y - 10,
        maxX: d.x + 10,
        maxY: d.y + 10,
        center: planeToGeo(d.x, d.y),
      },
      metadata: { custom: true },
    });
    spatialRegistry.contains(ODESSA_CITY.id, d.id);
  }

  // Streets (named arteries for Odessa twin)
  const streets = [
    { id: "str_deribasovskaya", name: "Deribasivska", x: 48, y: 36 },
    { id: "str_primorsky", name: "Prymorskyi Blvd", x: 52, y: 28 },
    { id: "str_industrial", name: "Industrial Ave", x: 24, y: 70 },
  ];
  for (const s of streets) {
    spatialRegistry.upsert({
      id: s.id,
      kind: "street",
      name: s.name,
      parentId: ODESSA_CITY.id,
      geo: planeToGeo(s.x, s.y),
      metadata: { odessa: true },
    });
    spatialRegistry.contains(ODESSA_CITY.id, s.id);
  }

  for (const b of CITY_BUILDINGS) {
    const buildingId = `spb_${b.id}`;
    const districtEntityId = `spd_${b.district}`;
    spatialRegistry.upsert({
      id: buildingId,
      kind: "building",
      name: b.label,
      parentId: districtEntityId,
      cityBuildingId: b.id,
      cityDistrictId: b.district,
      geo: planeToGeo(b.x + b.w / 2, b.y + b.h / 2),
      capacity: Math.round(b.w * b.h),
      metadata: { route: b.route, short: b.short, kind: b.kind || "building" },
    });
    spatialRegistry.contains(districtEntityId, buildingId);
    publishSpatialEvent("BuildingRegistered", {
      entityId: buildingId,
      buildingId: b.id,
      districtId: b.district,
    });

    // Floor + sample room/workspace for major buildings
    if (["hub", "developer", "ai_studio", "crm", "mission_control"].includes(b.id)) {
      const floorId = `spf_${b.id}_1`;
      spatialRegistry.upsert({
        id: floorId,
        kind: "floor",
        name: `${b.short} · Floor 1`,
        parentId: buildingId,
        cityBuildingId: b.id,
        geo: planeToGeo(b.x + b.w / 2, b.y + b.h / 2),
        metadata: { level: 1 },
      });
      spatialRegistry.contains(buildingId, floorId);

      const roomId = `spr_${b.id}_lobby`;
      spatialRegistry.upsert({
        id: roomId,
        kind: "room",
        name: `${b.short} Lobby`,
        parentId: floorId,
        cityBuildingId: b.id,
        geo: planeToGeo(b.x + b.w / 2, b.y + b.h / 2),
        metadata: { roomType: "lobby" },
      });
      spatialRegistry.contains(floorId, roomId);

      const wsId = `spw_${b.id}_desk`;
      spatialRegistry.upsert({
        id: wsId,
        kind: "workspace",
        name: `${b.short} Workspace`,
        parentId: roomId,
        cityBuildingId: b.id,
        geo: planeToGeo(b.x + b.w / 2, b.y + b.h / 2),
        metadata: { hotDesk: true },
      });
      spatialRegistry.contains(roomId, wsId);
    }
  }

  // Virtual space for remote work
  spatialRegistry.upsert({
    id: "spv_remote",
    kind: "virtual_space",
    name: "Remote Workplace Cloud",
    parentId: ODESSA_CITY.id,
    geo: { lat: ODESSA_CITY.lat, lng: ODESSA_CITY.lng, label: "Remote" },
    metadata: { virtual: true },
  });

  // POI
  spatialRegistry.upsert({
    id: "spo_port",
    kind: "poi",
    name: "Odessa Port Gate",
    parentId: "spd_logistics",
    geo: planeToGeo(18, 52),
    metadata: { poi: "port" },
  });

  // Street graph → connected buildings
  for (const edge of streetGraph()) {
    spatialRegistry.connected(`spb_${edge.from}`, `spb_${edge.to}`);
  }
  // Adjacent districts (sample)
  spatialRegistry.adjacent("spd_enterprise", "spd_crm");
  spatialRegistry.adjacent("spd_enterprise", "spd_finance");
  spatialRegistry.adjacent("spd_marketplace", "spd_production");

  routingEngine.rebuildNodes();
}
