import { describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import { messages } from "@/i18n/messages";
import { hubIntegrations } from "@/integrations/hub";
import { moduleRegistry, BUSINESS_ECOSYSTEM_KEYS } from "../../workspace/managers/moduleRegistry";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { applicationRegistry } from "../../navigation/managers/applicationRegistry";
import { telemetry } from "@/integrations/telemetry";

describe("Enterprise Web Foundation", () => {
  it("exposes version and stack readiness", () => {
    expect(webConfig.version).toBe("9.4.0");
    expect(webConfig.sprint).toBe("30.4");
    expect(webConfig.multiTenant).toBe(true);
    expect(webConfig.mfaReady).toBe(true);
    expect(webConfig.telemetryEnabled).toBeTypeOf("boolean");
    expect(webConfig.supportedLocales).toEqual(["en", "ru", "uk"]);
  });

  it("has localized strings", () => {
    expect(messages.en["nav.workspace"]).toBeTruthy();
    expect(messages.en["nav.navigation"]).toBeTruthy();
    expect(messages.en["nav.dashboard"]).toBeTruthy();
    expect(messages.ru["nav.dashboard"]).toBeTruthy();
    expect(messages.uk["nav.dashboard"]).toBeTruthy();
  });

  it("links enterprise integrations including observability", () => {
    expect(hubIntegrations.enterpriseHub).toContain("enterprise-hub");
    expect(hubIntegrations.webFoundation).toContain("enterprise-ewf");
    expect(hubIntegrations.designSystem).toContain("enterprise-eds");
    expect(hubIntegrations.identityCenter).toContain("enterprise-eic");
    expect(hubIntegrations.workspacePlatform).toContain("enterprise-ews");
    expect(hubIntegrations.navigationPlatform).toContain("enterprise-enp");
    expect(hubIntegrations.monitoring).toContain("enterprise-obs");
  });
});

describe("Sprint 30.4 Web Foundation", () => {
  it("registers all business ecosystem modules", () => {
    expect(BUSINESS_ECOSYSTEM_KEYS).toEqual([
      "auto",
      "beauty",
      "cafe",
      "agro",
      "drone",
      "legal",
      "crypto",
    ]);
    for (const key of BUSINESS_ECOSYSTEM_KEYS) {
      const meta = moduleRegistry.get(key);
      expect(meta).toBeTruthy();
      expect(moduleRegistry.routeFor(key)).toBe(`/workspace/${key}`);
    }
  });

  it("filters navigation by tenant permissions", () => {
    const limited = navigationManager.forTenant("demo", ["read"], "sidebar");
    expect(limited.some((i) => i.id === "nav_workspace")).toBe(true);
    expect(limited.some((i) => i.id === "nav_ecosystems")).toBe(true);
    const adminOnly = navigationManager.forTenant("demo", ["read"], "sidebar");
    expect(adminOnly.some((i) => i.id === "nav_identity")).toBe(false);
  });

  it("registers mission control and ecosystem apps", () => {
    expect(applicationRegistry.get("mission_control")?.route).toContain("mission-control");
    expect(applicationRegistry.get("beauty_enterprise")?.route).toBe("/workspace/beauty");
    expect(applicationRegistry.get("cafe_enterprise")?.route).toBe("/workspace/cafe");
    expect(applicationRegistry.get("drone_enterprise")?.route).toBe("/workspace/drone");
  });

  it("exposes telemetry helpers", () => {
    expect(typeof telemetry.log).toBe("function");
    expect(typeof telemetry.metric).toBe("function");
    expect(typeof telemetry.pageView).toBe("function");
    expect(typeof telemetry.audit).toBe("function");
  });
});
