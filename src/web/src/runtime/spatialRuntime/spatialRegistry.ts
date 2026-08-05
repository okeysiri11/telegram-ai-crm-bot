/**
 * Spatial entity registry + hierarchy — Sprint 29.4.
 */

import type {
  SpatialDistrictKind,
  SpatialEntity,
  SpatialEntityKind,
  SpatialRelationship,
  SpatialRelationKind,
  GeoLocation,
} from "./spatialTypes";
import { ODESSA_CITY } from "./spatialTypes";

const entities = new Map<string, SpatialEntity>();
const relationships = new Map<string, SpatialRelationship>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

/** Map city plane (0–100) → approx Odessa WGS84 delta */
export function planeToGeo(x: number, y: number): GeoLocation {
  // ~0.08° span around Odessa center for Digital Twin plane
  const lat = ODESSA_CITY.lat + (50 - y) * 0.0012;
  const lng = ODESSA_CITY.lng + (x - 50) * 0.0016;
  return { lat, lng, x, y };
}

export function districtKindForCityDistrict(cityDistrictId: string): SpatialDistrictKind {
  switch (cityDistrictId) {
    case "enterprise":
      return "business";
    case "crm":
    case "marketplace":
      return "marketplace";
    case "erp":
    case "production":
      return "industrial";
    case "finance":
    case "analytics":
      return "financial";
    case "knowledge":
      return "education";
    case "developer":
    case "ai":
      return "construction";
    case "security":
    case "settings":
      return "custom";
    default:
      return "custom";
  }
}

export const spatialRegistry = {
  clear() {
    entities.clear();
    relationships.clear();
  },

  upsert(input: Omit<SpatialEntity, "createdAt" | "updatedAt"> & { createdAt?: string }): SpatialEntity {
    const prev = entities.get(input.id);
    const entity: SpatialEntity = {
      ...input,
      metadata: input.metadata || {},
      createdAt: prev?.createdAt || input.createdAt || now(),
      updatedAt: now(),
    };
    entities.set(entity.id, entity);
    return entity;
  },

  get(id: string) {
    return entities.get(id);
  },

  list(kind?: SpatialEntityKind) {
    const all = [...entities.values()];
    return kind ? all.filter((e) => e.kind === kind) : all;
  },

  children(parentId: string) {
    return this.list().filter((e) => e.parentId === parentId);
  },

  ancestors(entityId: string): SpatialEntity[] {
    const chain: SpatialEntity[] = [];
    let cur = entities.get(entityId);
    const guard = new Set<string>();
    while (cur?.parentId && !guard.has(cur.parentId)) {
      guard.add(cur.parentId);
      const p = entities.get(cur.parentId);
      if (!p) break;
      chain.push(p);
      cur = p;
    }
    return chain;
  },

  relate(kind: SpatialRelationKind, fromId: string, toId: string, weight = 1): SpatialRelationship {
    const existing = [...relationships.values()].find(
      (r) => r.kind === kind && r.fromId === fromId && r.toId === toId,
    );
    if (existing) return existing;
    const rel: SpatialRelationship = {
      id: uid("srel"),
      kind,
      fromId,
      toId,
      weight,
      createdAt: now(),
    };
    relationships.set(rel.id, rel);
    return rel;
  },

  relations(entityId?: string, kind?: SpatialRelationKind) {
    let all = [...relationships.values()];
    if (entityId) all = all.filter((r) => r.fromId === entityId || r.toId === entityId);
    if (kind) all = all.filter((r) => r.kind === kind);
    return all;
  },

  contains(containerId: string, childId: string) {
    return this.relate("contains", containerId, childId);
  },

  connected(a: string, b: string, weight = 1) {
    this.relate("connected", a, b, weight);
    this.relate("connected", b, a, weight);
  },

  adjacent(a: string, b: string) {
    this.relate("adjacent", a, b);
    this.relate("adjacent", b, a);
  },
};
