import { beforeEach, describe, expect, it } from "vitest";
import {
  CITY_BUILDINGS,
  CITY_DISTRICTS,
  CITY_STATUS_SEED,
  buildingsByDistrict,
  buildingOps,
  cityNavigation,
  clampViewport,
  getBuilding,
  getPlaza,
  healthFromLiveTone,
  HEALTH_LABEL_RU,
  panToBuilding,
  searchBuildings,
  streetGraph,
  viewportRect,
} from "./index";
import { CITY_VIEWPORT_KEY } from "./cityEngine";
import { createPerformanceMonitor } from "./graphics/performanceMonitor";

describe("Sprint 30.4 Enterprise City Visualization Beta", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it("exposes all 16 Beta districts", () => {
    const ids = CITY_DISTRICTS.map((d) => d.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "settings",
        "crm",
        "erp",
        "finance",
        "production",
        "warehouse",
        "legal",
        "marketing",
        "ai",
        "security",
        "analytics",
        "documents",
        "marketplace",
        "knowledge",
        "developer",
        "enterprise",
      ]),
    );
    expect(CITY_DISTRICTS).toHaveLength(16);
    expect(CITY_DISTRICTS.every((d) => !!d.labelRu)).toBe(true);
  });

  it("maps buildings to existing routes only", () => {
    expect(CITY_BUILDINGS.length).toBeGreaterThanOrEqual(20);
    expect(CITY_BUILDINGS.every((b) => b.route.startsWith("/"))).toBe(true);
    expect(getBuilding("erp")?.route).toBe("/erp");
    expect(getBuilding("marketplace")?.route).toBe("/marketplace");
    expect(getBuilding("security")?.route).toBe("/identity/security");
    expect(getBuilding("developer")?.route).toBe("/command-center");
    expect(getBuilding("warehouse")?.route).toContain("/erp");
    expect(getBuilding("legal")?.route).toBe("/workspace/legal");
    expect(getBuilding("finance")?.route).toContain("finance");
    expect(getPlaza()?.kind).toBe("plaza");
  });

  it("has AI assistant and ops metadata on each building", () => {
    expect(CITY_BUILDINGS.every((b) => !!b.aiAssistant)).toBe(true);
    for (const b of CITY_BUILDINGS) {
      const ops = buildingOps(b.id, b.route);
      expect(ops.owner.length).toBeGreaterThan(0);
      expect(ops.activeUsers).toBeGreaterThanOrEqual(0);
      expect(ops.description.length).toBeGreaterThan(0);
      expect(ops.quickActions.length).toBeGreaterThan(0);
      expect(HEALTH_LABEL_RU[ops.health]).toBeTruthy();
    }
  });

  it("derives live health tones", () => {
    expect(healthFromLiveTone("alert", 0, 0)).toBe("critical");
    expect(healthFromLiveTone("active", 5, 0)).toBe("warning");
    expect(healthFromLiveTone("idle", 0, 0)).toBe("maintenance");
    expect(healthFromLiveTone("busy", 0, 1)).toBe("online");
  });

  it("searches buildings and districts", () => {
    expect(searchBuildings("crm").some((b) => b.id === "crm")).toBe(true);
    expect(searchBuildings("plaza").some((b) => b.id === "plaza")).toBe(true);
    expect(searchBuildings("склад").some((b) => b.id === "warehouse")).toBe(true);
    expect(searchBuildings("casino").some((b) => b.id === "casino")).toBe(true);
    expect(searchBuildings("казино").some((b) => b.id === "casino")).toBe(true);
    expect(getBuilding("casino")?.route).toBe("/casino/venues/odessa-prime");
    expect(buildingOps("casino").quickActions[0]?.label).toBe("Войти в казино");
    expect(buildingOps("casino").quickActions[0]?.route).toBe("/casino");
    expect(buildingsByDistrict("ai").length).toBeGreaterThanOrEqual(2);
    expect(buildingsByDistrict("warehouse").length).toBeGreaterThanOrEqual(1);
    expect(buildingsByDistrict("legal").length).toBeGreaterThanOrEqual(1);
  });

  it("provides street graph from plaza", () => {
    const links = streetGraph();
    expect(links.length).toBeGreaterThan(10);
    expect(links.some((l) => l.from === "plaza" || l.to === "plaza")).toBe(true);
    expect(links.some((l) => l.from === "warehouse" || l.to === "warehouse")).toBe(true);
  });

  it("clamps camera viewport and pans to buildings", () => {
    const v = clampViewport({ x: 99, y: -99, zoom: 5 });
    expect(v.x).toBeLessThanOrEqual(35);
    expect(v.y).toBeGreaterThanOrEqual(-35);
    expect(v.zoom).toBeLessThanOrEqual(1.75);
    const crm = getBuilding("crm")!;
    const pan = panToBuilding(crm);
    expect(pan.zoom).toBeGreaterThan(1);
    const rect = viewportRect(pan);
    expect(rect.width).toBeGreaterThan(0);
    expect(rect.height).toBeGreaterThan(0);
    expect(CITY_VIEWPORT_KEY).toBe("ews_city_viewport_v1");
  });

  it("tracks history recent favorites and Russian breadcrumbs", () => {
    cityNavigation.pushHistory("crm");
    cityNavigation.pushHistory("erp");
    expect(cityNavigation.history()[0]).toBe("erp");
    expect(cityNavigation.recent()).toContain("crm");
    expect(cityNavigation.toggleFavorite("knowledge")).toBe(true);
    expect(cityNavigation.isFavorite("knowledge")).toBe(true);
    expect(cityNavigation.toggleFavorite("knowledge")).toBe(false);
    const crumbs = cityNavigation.breadcrumbs(getBuilding("crm")!);
    expect(crumbs.map((c) => c.label)).toEqual(
      expect.arrayContaining(["Город предприятия", "CRM", "CRM Center"]),
    );
    const wh = cityNavigation.breadcrumbs(getBuilding("warehouse")!);
    expect(wh[0]?.label).toBe("Город предприятия");
    expect(wh.some((c) => c.label === "Склад")).toBe(true);
  });

  it("seeds live status for every building", () => {
    for (const b of CITY_BUILDINGS) {
      expect(CITY_STATUS_SEED[b.id]).toBeTruthy();
    }
  });

  it("keeps performance monitor sample path fast", () => {
    const monitor = createPerformanceMonitor();
    const t0 = performance.now();
    for (let i = 0; i < 200; i++) {
      monitor.measureFrame(() => {
        monitor.measureRender(() => CITY_BUILDINGS.length + CITY_DISTRICTS.length);
      });
    }
    const elapsed = performance.now() - t0;
    expect(elapsed).toBeLessThan(500);
    const snap = monitor.snapshot();
    expect(snap.cpuTimeMs).toBeGreaterThanOrEqual(0);
    expect(snap.renderTimeMs).toBeGreaterThanOrEqual(0);
  });
});
