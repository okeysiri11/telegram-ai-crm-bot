import { describe, expect, it } from "vitest";
import { ENTERPRISE_MODULES, getModuleBySlug } from "@/modules/moduleCatalog";
import { ENTERPRISE_SHELL_NAV } from "@/shell/enterprise/enterpriseNav";

describe("Sprint 27.2 enterprise navigation", () => {
  it("exposes clean module URLs in the shell nav", () => {
    const routes = ENTERPRISE_SHELL_NAV.map((n) => n.route);
    for (const required of [
      "/dashboard",
      "/crm",
      "/erp",
      "/projects",
      "/ai-studio",
      "/ai-agents",
      "/knowledge",
      "/documents",
      "/analytics",
      "/marketplace",
      "/automation",
      "/integrations",
      "/security",
      "/settings",
    ]) {
      expect(routes).toContain(required);
    }
  });

  it("registers a hub definition for every shell module except settings deep page", () => {
    expect(getModuleBySlug("crm")?.route).toBe("/crm");
    expect(getModuleBySlug("ai_studio")?.route).toBe("/ai-studio");
    expect(getModuleBySlug("city")?.readiness).toBe("coming_soon");
    expect(ENTERPRISE_MODULES.every((m) => m.quickActions.length > 0)).toBe(true);
    expect(ENTERPRISE_MODULES.every((m) => m.roadmap.length > 0)).toBe(true);
  });
});
