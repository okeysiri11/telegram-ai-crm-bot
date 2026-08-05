/**
 * Sprint 31.1 — Visual polish, interactive city UX, Owner God Mode, role dashboards.
 * Naming note: Agriculture Pilot also uses 31.1 — these tests cover the web UX track.
 */
import { describe, expect, it } from "vitest";
import { deriveGodModeMetrics } from "@/enterprise-business/deriveGodModeMetrics";
import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { CITY_DISTRICTS } from "@/enterprise-city/cityDistricts";
import { zoomBy, applyPanDelta, viewportRect, readViewport } from "@/enterprise-city/cityEngine";
import { OWNER_RU_NAV } from "@/navigation/enterpriseRuNav";
import { webConfig } from "@/config/webConfig";

describe("Sprint 31.1 Visual Polish & Enterprise City UX", () => {
  it("keeps God Mode and city polish surfaces after later sprints", () => {
    expect(Number.parseFloat(webConfig.sprint)).toBeGreaterThanOrEqual(31.1);
  });

  it("God Mode metrics cover required ops surfaces", () => {
    const cards = deriveGodModeMetrics();
    const ids = cards.map((c) => c.id);
    for (const required of [
      "platform_health",
      "ai_runtime",
      "queues",
      "workers",
      "users",
      "organizations",
      "sessions",
      "errors",
      "warnings",
      "cpu",
      "memory",
      "api",
      "database",
      "redis",
    ]) {
      expect(ids).toContain(required);
    }
    expect(cards.every((c) => c.title && c.route.startsWith("/"))).toBe(true);
  });

  it("Enterprise City catalog is navigable with districts and buildings", () => {
    expect(CITY_BUILDINGS.length).toBeGreaterThan(10);
    expect(CITY_DISTRICTS.length).toBeGreaterThan(3);
    expect(CITY_BUILDINGS.every((b) => typeof b.route === "string" && b.route.length > 0)).toBe(true);
  });

  it("city camera supports zoom, pan, and minimap viewport math", () => {
    const base = readViewport();
    const zoomed = zoomBy(base, 0.2);
    expect(zoomed.zoom).toBeGreaterThan(base.zoom);
    const panned = applyPanDelta(zoomed, 4, -3);
    expect(panned.x).not.toBe(zoomed.x);
    const rect = viewportRect(panned);
    expect(rect.width).toBeGreaterThan(0);
    expect(rect.height).toBeGreaterThan(0);
  });

  it("exports City preview panel (live city CTA)", async () => {
    expect(typeof (await import("@/enterprise-city/CityPreviewPanel")).CityPreviewPanel).toBe(
      "function",
    );
  });

  it("role dashboards and polish strip export", async () => {
    expect(typeof (await import("@/dashboard/RoleDashboardPolish")).RoleDashboardPolish).toBe(
      "function",
    );
    expect(typeof (await import("@/dashboard/AdminDashboardPage")).AdminDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("@/dashboard/RoleOpsDashboards")).ManagerDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("@/dashboard/ClientDashboardPage")).ClientDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("@/dashboard/DealerDashboardPage")).DealerDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("@/navigation/OwnerDashboardPage")).OwnerDashboardPage).toBe(
      "function",
    );
  }, 20_000);

  it("Russian nav labels God Mode as Режим владельца", () => {
    const god = OWNER_RU_NAV.find((i) => i.id === "owner_god");
    expect(god?.label).toBe("Режим владельца");
    expect(god?.route).toBe("/platform-builder/god-mode");
  });

  it("AI Studio and Production Studio pages remain composed surfaces", async () => {
    expect(typeof (await import("@/ai-studio/AIStudioPage")).AIStudioPage).toBe("function");
    expect(
      typeof (await import("@/ai-production-studio/AIProductionCenterPage")).AIProductionCenterPage,
    ).toBe("function");
  });
});
