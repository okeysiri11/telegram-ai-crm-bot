/**
 * Routing foundation — Sprint 29.4.
 * Graph over spatial connected/adjacent edges + city street graph.
 * Future: traffic + vehicle modes.
 */

import type { GeoLocation, NavigationNode, SpatialRoute } from "./spatialTypes";
import { spatialRegistry, planeToGeo } from "./spatialRegistry";

const nodes = new Map<string, NavigationNode>();
const routeCache = new Map<string, SpatialRoute>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function haversineM(a: GeoLocation, b: GeoLocation): number {
  const R = 6371000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

function walkSec(distanceM: number) {
  // ~4.5 km/h walking
  return Math.max(30, Math.round((distanceM / 4500) * 3600));
}

function straightRoute(
  fromEntityId: string,
  toEntityId: string,
  mode: SpatialRoute["mode"],
  cacheKey: string,
): SpatialRoute {
  const a = spatialRegistry.get(fromEntityId)?.geo || planeToGeo(40, 40);
  const b = spatialRegistry.get(toEntityId)?.geo || planeToGeo(60, 60);
  const distanceM = haversineM(a, b);
  const route: SpatialRoute = {
    id: uid("rt"),
    fromEntityId,
    toEntityId,
    nodeIds: [fromEntityId, toEntityId],
    path: [a, b],
    distanceM,
    travelTimeSec: mode === "vehicle" ? Math.round(walkSec(distanceM) * 0.35) : walkSec(distanceM),
    mode: mode === "walk" ? "virtual" : mode,
  };
  routeCache.set(cacheKey, route);
  return route;
}

export const routingEngine = {
  clear() {
    nodes.clear();
    routeCache.clear();
  },

  rebuildNodes() {
    nodes.clear();
    const buildings = spatialRegistry.list("building");
    for (const b of buildings) {
      const geo = b.geo || planeToGeo(50, 50);
      nodes.set(b.id, { id: `nav_${b.id}`, entityId: b.id, geo, edges: [] });
    }
    // edges from connected relationships
    for (const rel of spatialRegistry.relations(undefined, "connected")) {
      const from = nodes.get(rel.fromId);
      const to = nodes.get(rel.toId);
      if (!from || !to) continue;
      const distanceM = haversineM(from.geo, to.geo) * (rel.weight || 1);
      if (!from.edges.some((e) => e.toNodeId === to.id)) {
        from.edges.push({
          toNodeId: to.id,
          distanceM,
          travelSec: walkSec(distanceM),
        });
      }
    }
    return this.listNodes();
  },

  listNodes() {
    return [...nodes.values()];
  },

  getNode(entityId: string) {
    return nodes.get(entityId);
  },

  /** Dijkstra shortest path between building entities */
  route(
    fromEntityId: string,
    toEntityId: string,
    mode: SpatialRoute["mode"] = "walk",
  ): SpatialRoute | null {
    const cacheKey = `${fromEntityId}->${toEntityId}:${mode}`;
    const cached = routeCache.get(cacheKey);
    if (cached) return cached;

    if (!nodes.size) this.rebuildNodes();
    const start = nodes.get(fromEntityId);
    const goal = nodes.get(toEntityId);
    if (fromEntityId === toEntityId) {
      const geo = start?.geo || spatialRegistry.get(fromEntityId)?.geo || planeToGeo(50, 50);
      const route: SpatialRoute = {
        id: uid("rt"),
        fromEntityId,
        toEntityId,
        nodeIds: [fromEntityId],
        path: [geo],
        distanceM: 0,
        travelTimeSec: 0,
        mode,
      };
      routeCache.set(cacheKey, route);
      return route;
    }

    if (!start || !goal) {
      return straightRoute(fromEntityId, toEntityId, mode, cacheKey);
    }

    const dist = new Map<string, number>();
    const prev = new Map<string, string>();
    const q = new Set(nodes.keys());
    for (const id of q) dist.set(id, Infinity);
    dist.set(fromEntityId, 0);

    while (q.size) {
      let u: string | null = null;
      let best = Infinity;
      for (const id of q) {
        const d = dist.get(id) ?? Infinity;
        if (d < best) {
          best = d;
          u = id;
        }
      }
      if (!u || best === Infinity) break;
      q.delete(u);
      if (u === toEntityId) break;
      const node = nodes.get(u);
      if (!node) continue;
      for (const e of node.edges) {
        const peerEntity = [...nodes.values()].find((n) => n.id === e.toNodeId)?.entityId;
        if (!peerEntity || !q.has(peerEntity)) continue;
        const alt = best + e.distanceM;
        if (alt < (dist.get(peerEntity) ?? Infinity)) {
          dist.set(peerEntity, alt);
          prev.set(peerEntity, u);
        }
      }
    }

    if (!prev.has(toEntityId) && fromEntityId !== toEntityId) {
      return straightRoute(fromEntityId, toEntityId, mode === "walk" ? "virtual" : mode, cacheKey);
    }

    const nodeIds: string[] = [toEntityId];
    let walk = toEntityId;
    while (walk !== fromEntityId) {
      const p = prev.get(walk);
      if (!p) break;
      nodeIds.push(p);
      walk = p;
    }
    nodeIds.reverse();
    const path = nodeIds.map((id) => nodes.get(id)?.geo || planeToGeo(50, 50));
    const distanceM = dist.get(toEntityId) || 0;
    const route: SpatialRoute = {
      id: uid("rt"),
      fromEntityId,
      toEntityId,
      nodeIds,
      path,
      distanceM,
      travelTimeSec:
        mode === "vehicle" ? Math.round(walkSec(distanceM) * 0.35) : walkSec(distanceM),
      mode,
    };
    routeCache.set(cacheKey, route);
    return route;
  },

  distance(fromEntityId: string, toEntityId: string) {
    const r = this.route(fromEntityId, toEntityId);
    return r?.distanceM ?? 0;
  },

  travelTime(fromEntityId: string, toEntityId: string, mode: SpatialRoute["mode"] = "walk") {
    const r = this.route(fromEntityId, toEntityId, mode);
    return r?.travelTimeSec ?? 0;
  },

  cachedCount() {
    return routeCache.size;
  },
};
