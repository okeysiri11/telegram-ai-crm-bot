/**
 * Sprint 30.6 — Platform integration tests (boot, routes, demo, health, city districts).
 */

import { describe, expect, it } from "vitest";
import {
  assertBootCoverage,
  BETA_LIVE_DEMO_STEPS,
  BETA_LIVE_DEMO_META,
  BOOT_ENTRY_ROUTES,
  derivePlatformHealth,
  INTEGRATION_ROUTES,
  OWNER_SUBSYSTEMS,
  PLATFORM_BOOT_VERSION,
  requiredBootPaths,
} from "./index";
import {
  CITY_DISTRICTS,
  DISTRICT_PRIMARY_BUILDING,
  getBuilding,
  primaryBuildingForDistrict,
} from "@/enterprise-city";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { PRODUCTION_QUICK_ACTIONS_RU, PRODUCTION_STUDIOS } from "@/ai-production-studio/productionCatalog";
import { createPerformanceMonitor } from "@/enterprise-city/graphics/performanceMonitor";
import { ROLE_SWITCHER_OPTIONS } from "@/navigation/enterpriseRuNav";

/** Paths known registered in App.tsx for smoke coverage (static check). */
const REGISTERED_PATHS = [
  "/",
  "/login",
  "/dashboard",
  "/city",
  "/enterprise-city",
  "/ai",
  "/ai-agents",
  "/production",
  "/production-studio",
  "/crm",
  "/erp",
  "/analytics",
  "/settings",
  "/owner",
  "/knowledge",
  "/health",
  "/demo/scenario",
  "/errors/404",
  "/errors/403",
  "/errors/500",
  "/errors/offline",
  "/errors/unauthorized",
];

describe("Sprint 30.6 Platform Integration", () => {
  it("boots with versioned entry routes", () => {
    expect(PLATFORM_BOOT_VERSION).toBe("30.6");
    expect(BOOT_ENTRY_ROUTES.map((r) => r.path)).toEqual([
      "/",
      "/login",
      "/dashboard",
      "/city",
      "/ai",
      "/production",
      "/settings",
    ]);
    const check = assertBootCoverage(REGISTERED_PATHS);
    expect(check.ok).toBe(true);
    expect(check.missing).toEqual([]);
    expect(requiredBootPaths().length).toBe(INTEGRATION_ROUTES.length);
  });

  it("maps city districts to real module buildings", () => {
    const requiredDistricts = [
      "settings",
      "crm",
      "erp",
      "enterprise",
      "finance",
      "marketing",
      "legal",
      "warehouse",
      "analytics",
      "production",
      "ai",
    ] as const;
    for (const id of requiredDistricts) {
      expect(CITY_DISTRICTS.some((d) => d.id === id)).toBe(true);
      const b = primaryBuildingForDistrict(id);
      expect(b).toBeTruthy();
      expect(b!.route.startsWith("/")).toBe(true);
      expect(DISTRICT_PRIMARY_BUILDING[id]).toBeTruthy();
    }
    expect(getBuilding("crm")?.route).toBe("/crm");
    expect(getBuilding("production")?.route).toContain("production");
    expect(getBuilding("ai_team")?.route).toBe("/ai-agents");
  });

  it("exposes beta live demo path", () => {
    expect(BETA_LIVE_DEMO_META.sprint).toBe("30.6");
    expect(BETA_LIVE_DEMO_STEPS.map((s) => s.id)).toEqual([
      "login",
      "dashboard",
      "city",
      "building",
      "ai_agent",
      "production",
      "generate",
      "result",
    ]);
    expect(BETA_LIVE_DEMO_STEPS.every((s) => s.route.startsWith("/"))).toBe(true);
  });

  it("owner subsystems cover platform surfaces", () => {
    const ids = OWNER_SUBSYSTEMS.map((s) => s.id);
    expect(ids).toEqual(
      expect.arrayContaining(["status", "users", "agents", "projects", "knowledge", "logs", "runtime"]),
    );
  });

  it("derives platform health metrics", () => {
    const h = derivePlatformHealth();
    expect(h.cpuPct).toBeGreaterThanOrEqual(0);
    expect(h.memoryPct).toBeGreaterThanOrEqual(0);
    expect(h.items.length).toBeGreaterThan(0);
    expect(["healthy", "warning", "critical", "offline"]).toContain(h.level);
  });

  it("keeps AI and Production integration surfaces", () => {
    expect(DEFAULT_AGENTS.length).toBeGreaterThanOrEqual(10);
    expect(PRODUCTION_STUDIOS.length).toBeGreaterThanOrEqual(20);
    expect(PRODUCTION_QUICK_ACTIONS_RU.length).toBe(6);
  });

  it("role switcher includes owner", () => {
    expect(ROLE_SWITCHER_OPTIONS.some((r) => r.id === "owner")).toBe(true);
  });

  it("performance sample stays fast for smoke", () => {
    const monitor = createPerformanceMonitor();
    const t0 = performance.now();
    for (let i = 0; i < 100; i++) {
      monitor.measureFrame(() => monitor.measureRender(() => REGISTERED_PATHS.length));
    }
    expect(performance.now() - t0).toBeLessThan(400);
  });
});
