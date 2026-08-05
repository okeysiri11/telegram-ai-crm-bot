/**
 * Object catalog + search/navigation — Sprint 29.6.
 * Built from live runtimes (no mocks).
 */

import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { cityNavigation } from "@/enterprise-city/cityNavigation";
import { spatialRuntime, resolveSpatialBuildingId } from "@/runtime/spatialRuntime";
import { lifeEngine } from "@/runtime/lifeEngine";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { assetRuntime } from "@/runtime/assetRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import type { InteractionTarget, NavigationEntry, SearchHit } from "./interactionTypes";
import { interactionRegistry } from "./interactionRegistry";
import { interactionCache } from "./interactionCache";
import { publishInteractionEvent } from "./interactionEvents";
import { interactionHistory } from "./interactionSession";

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

const navHistory: NavigationEntry[] = [];

export function buildObjectCatalog(): InteractionTarget[] {
  spatialRuntime.startup();
  lifeEngine.startup();
  digitalCitizenEngine.startup();
  businessNetworkEngine.startup();
  assetRuntime.startup();
  cityVisualizationRuntime.startup();

  const key = [
    spatialRuntime.stats().entities,
    digitalCitizenEngine.listCitizens().length,
    businessNetworkEngine.listProfiles().length,
    assetRuntime.stats().assets,
    lifeEngine.meetings.list().length,
  ].join(":");

  if (interactionCache.catalogValid(key)) return interactionCache.getCatalog();

  const targets: InteractionTarget[] = [];

  for (const b of CITY_BUILDINGS) {
    targets.push({
      kind: "building",
      id: b.id,
      label: b.label,
      buildingId: b.id,
      districtId: b.district,
      route: b.route || interactionRegistry.defaultRoute("building"),
      meta: { x: b.x + b.w / 2, y: b.y + b.h / 2, short: b.short },
    });
  }

  for (const d of spatialRuntime.list("district")) {
    targets.push({
      kind: "district",
      id: d.cityDistrictId || d.id,
      label: d.name,
      districtId: d.cityDistrictId || d.id,
      route: interactionRegistry.defaultRoute("district"),
      meta: { spatialEntityId: d.id, kind: d.districtKind, x: d.geo?.x, y: d.geo?.y },
    });
  }

  for (const p of businessNetworkEngine.listProfiles()) {
    const buildingId = p.metadata?.cityBuilding ? String(p.metadata.cityBuilding) : undefined;
    targets.push({
      kind: "company",
      id: p.id,
      label: p.companyName,
      companyId: p.id,
      buildingId,
      route: interactionRegistry.defaultRoute("company"),
      meta: { category: p.category },
    });
  }

  for (const c of digitalCitizenEngine.listCitizens()) {
    targets.push({
      kind: "citizen",
      id: c.id,
      label: c.displayName,
      buildingId: c.presence.cityBuildingId,
      companyId: digitalCitizenEngine.listMemberships(c.id)[0]?.orgId,
      route: interactionRegistry.defaultRoute("citizen"),
      meta: { presence: c.presence.status },
    });
  }

  for (const a of digitalCitizenEngine.listAi()) {
    targets.push({
      kind: "ai_agent",
      id: a.id,
      label: a.name,
      companyId: undefined,
      route: interactionRegistry.defaultRoute("ai_agent"),
      meta: { kind: a.kind, assignedCitizenId: a.assignedCitizenId, active: a.active },
    });
  }

  for (const a of assetRuntime.list()) {
    const isVehicle = a.type === "vehicle" || a.type === "drone";
    targets.push({
      kind: isVehicle ? "vehicle" : "asset",
      id: a.id,
      label: a.profile.name,
      buildingId: a.location.buildingId,
      districtId: a.location.districtId,
      companyId: a.ownership.companyId,
      route: interactionRegistry.defaultRoute(isVehicle ? "vehicle" : "asset"),
      meta: { type: a.type, status: a.status, available: a.available },
    });
  }

  for (const m of lifeEngine.meetings.list()) {
    targets.push({
      kind: "meeting",
      id: m.id,
      label: m.title,
      buildingId: m.buildingId,
      companyId: m.companyId,
      route: interactionRegistry.defaultRoute("meeting"),
      meta: { status: m.status },
    });
  }

  for (const p of lifeEngine.cityRuntime().projects) {
    targets.push({
      kind: "project",
      id: p.projectId,
      label: p.projectName,
      buildingId: "hub",
      route: interactionRegistry.defaultRoute("project"),
      meta: { memberCount: p.memberCount, status: p.status },
    });
  }

  for (const v of lifeEngine.vehicles.list()) {
    if (targets.some((t) => t.kind === "vehicle" && t.meta?.lifeVehicleId === v.id)) continue;
    targets.push({
      kind: "vehicle",
      id: v.id,
      label: v.label,
      buildingId: v.toBuildingId || v.fromBuildingId,
      route: interactionRegistry.defaultRoute("vehicle"),
      meta: { lifeVehicleId: v.id, status: v.status },
    });
  }

  return interactionCache.putCatalog(key, targets);
}

function scoreLabel(query: string, label: string, id: string): number {
  const q = query.toLowerCase();
  const l = label.toLowerCase();
  const i = id.toLowerCase();
  if (i === q || l === q) return 100;
  if (l.startsWith(q) || i.startsWith(q)) return 80;
  if (l.includes(q) || i.includes(q)) return 50;
  const tokens = q.split(/\s+/).filter(Boolean);
  let s = 0;
  for (const t of tokens) {
    if (l.includes(t) || i.includes(t)) s += 20;
  }
  return s;
}

export const navigationEngine = {
  clear() {
    navHistory.length = 0;
  },

  catalog() {
    return buildObjectCatalog();
  },

  find(kind: InteractionTarget["kind"], id: string) {
    return this.catalog().find((t) => t.kind === kind && t.id === id);
  },

  globalSearch(query: string, limit = 20): SearchHit[] {
    const q = query.trim();
    if (!q) return [];
    const cached = interactionCache.getSearch(`g:${q}`);
    if (cached) return cached.slice(0, limit);
    const hits: SearchHit[] = [];
    for (const t of this.catalog()) {
      const score = scoreLabel(q, t.label, t.id);
      if (score > 0) hits.push({ target: t, score, source: "global" });
    }
    hits.sort((a, b) => b.score - a.score);
    const out = hits.slice(0, limit);
    interactionCache.putSearch(`g:${q}`, out);
    interactionHistory.recordEvent("search", { message: q, payload: { hits: out.length } });
    return out;
  },

  contextSearch(query: string, kind?: InteractionTarget["kind"], limit = 20): SearchHit[] {
    const base = this.globalSearch(query, 80);
    const filtered = kind ? base.filter((h) => h.target.kind === kind) : base;
    return filtered.slice(0, limit).map((h) => ({ ...h, source: "context" as const }));
  },

  nearby(buildingId: string, limit = 12): SearchHit[] {
    const catalog = this.catalog();
    const origin = catalog.find((t) => t.kind === "building" && t.id === buildingId);
    if (!origin) {
      return catalog
        .filter((t) => t.buildingId === buildingId)
        .slice(0, limit)
        .map((t) => ({ target: t, score: 40, source: "nearby" as const }));
    }
    const fromEntity = resolveSpatialBuildingId(buildingId);
    const scored: SearchHit[] = [];
    for (const t of catalog) {
      if (t.kind === "building" && t.id === buildingId) continue;
      if (t.buildingId === buildingId || t.districtId === origin.districtId) {
        let score = t.buildingId === buildingId ? 70 : 40;
        if (t.kind === "building") {
          const toEntity = resolveSpatialBuildingId(t.id);
          const dist = spatialRuntime.distance(fromEntity, toEntity);
          score = Math.max(10, 90 - Math.min(80, dist / 20));
        }
        scored.push({ target: t, score, source: "nearby" });
      }
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit);
  },

  businessDiscovery(query = "", limit = 20): SearchHit[] {
    const q = query.trim().toLowerCase();
    const companies = this.catalog().filter((t) => t.kind === "company");
    const hits = companies
      .map((t) => ({
        target: t,
        score: q ? scoreLabel(q, t.label, t.id) : 30,
        source: "business" as const,
      }))
      .filter((h) => h.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
    return hits;
  },

  pushNavigation(path: string, target?: InteractionTarget, label?: string) {
    const entry: NavigationEntry = {
      id: uid("nav"),
      at: now(),
      path,
      target,
      label: label || target?.label || path,
    };
    navHistory.unshift(entry);
    if (navHistory.length > 40) navHistory.length = 40;
    if (target?.kind === "building") {
      try {
        cityNavigation.pushHistory(target.id as Parameters<typeof cityNavigation.pushHistory>[0]);
      } catch {
        /* city nav optional */
      }
    }
    publishInteractionEvent("NavigationChanged", {
      path,
      targetId: target?.id,
      targetKind: target?.kind,
    });
    interactionHistory.recordEvent("navigate", {
      target,
      message: path,
      result: "ok",
    });
    return entry;
  },

  history(limit = 20) {
    return navHistory.slice(0, limit);
  },

  quickJump(kind: InteractionTarget["kind"], id: string) {
    const target = this.find(kind, id);
    if (!target) return null;
    const path = target.route || interactionRegistry.defaultRoute(kind);
    this.pushNavigation(path, target, target.label);
    return { target, path };
  },
};
