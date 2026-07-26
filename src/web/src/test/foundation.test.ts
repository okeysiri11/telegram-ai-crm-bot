import { describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import { messages } from "@/i18n/messages";
import { hubIntegrations } from "@/integrations/hub";
import {
  moduleRegistry,
  BUSINESS_ECOSYSTEM_KEYS,
} from "../../workspace/managers/moduleRegistry";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { applicationRegistry } from "../../navigation/managers/applicationRegistry";
import { telemetry } from "@/integrations/telemetry";
import { sharedUiChecklist } from "@/ui/sharedUi";

describe("Enterprise Web Foundation", () => {
  it("exposes version and stack readiness", () => {
    expect(webConfig.version).toBe("9.4.0");
    expect(webConfig.sprint).toBe("30.9");
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

describe("Sprint 30.5 Web Core Integration", () => {
  it("registers full module metadata for ecosystems", () => {
    expect(moduleRegistry.ecosystemsRegistered()).toBe(true);
    for (const key of BUSINESS_ECOSYSTEM_KEYS) {
      const m = moduleRegistry.get(key)!;
      expect(m.name).toBeTruthy();
      expect(m.version).toBeTruthy();
      expect(m.routes[0]).toBe(`/workspace/${key}`);
      expect(m.permissions.length).toBeGreaterThan(0);
      expect(m.navigation.length).toBeGreaterThan(0);
      expect(m.widgets.length).toBeGreaterThan(0);
      expect(m.dashboards.length).toBeGreaterThan(0);
      expect(m.dependencies.length).toBeGreaterThan(0);
      expect(m.health).toBe("healthy");
    }
  });

  it("registers mission control and pilot platform modules", () => {
    expect(moduleRegistry.get("mission_control")?.routes).toContain(
      "/platform-builder/mission-control",
    );
    expect(moduleRegistry.get("pilot")?.routes).toContain("/pilot");
  });

  it("derives application registry from module registry", () => {
    expect(applicationRegistry.get("auto_marketplace")?.route).toBe("/workspace/auto");
    expect(applicationRegistry.get("pilot_dashboard")?.route).toBe("/pilot");
    expect(applicationRegistry.get("mission_control")?.route).toContain("mission-control");
  });

  it("filters navigation by tenant permissions", () => {
    const limited = navigationManager.forTenant("demo", ["read"], "sidebar");
    expect(limited.some((i) => i.id === "nav_workspace")).toBe(true);
    expect(limited.some((i) => i.id === "nav_ecosystems")).toBe(true);
    expect(limited.some((i) => i.id === "nav_identity")).toBe(false);
  });

  it("exposes shared UI checklist and telemetry helpers", () => {
    expect(sharedUiChecklist().length).toBeGreaterThan(5);
    expect(typeof telemetry.healthSnapshot).toBe("function");
    expect(typeof telemetry.businessEvent).toBe("function");
    expect(typeof telemetry.audit).toBe("function");
  });
});

describe("Sprint 30.6 First Live Workflow", () => {
  it("uses production sprint tag and rejects demo auth config", async () => {
    expect(webConfig.autoPrefix).toContain("/api/auto/v1");
    const { isJwtToken } = await import("@/auth/identityApi");
    expect(isJwtToken("jwt.foo.demo")).toBe(false);
    expect(isJwtToken("a.b.c")).toBe(true);
  });
});

describe("Sprint 30.7 Pilot Hardening", () => {
  it("exposes feedback triage and role journeys", async () => {
    const { assignModule, classifySeverity } = await import("@/integrations/pilotFeedback");
    expect(assignModule("lead creation failed in crm")).toBe("automotive");
    expect(classifySeverity("error", "error", "critical outage")).toBe("Critical");
    const { PILOT_ROLE_JOURNEYS, validateJourneys } = await import("../pilot/roleJourneys");
    expect(PILOT_ROLE_JOURNEYS.length).toBe(5);
    const v = validateJourneys({
      authenticated: true,
      roleId: "platform_owner",
      roles: ["owner"],
    });
    expect(v.some((j) => j.role === "owner" && j.roleMatch)).toBe(true);
  });
});

describe("Sprint 30.8 Beauty Pilot Foundation", () => {
  it("wires beauty prefixes and ecosystem template", async () => {
    expect(webConfig.beautyOsPrefix).toContain("enterprise-bos");
    expect(webConfig.beautyWorkspacePrefix).toContain("enterprise-bws");
    expect(webConfig.beautyClientJourneyPrefix).toContain("enterprise-bcj");
    expect(hubIntegrations.beautyOs).toContain("enterprise-bos");
    const { ECOSYSTEM_REUSE_MATRIX } = await import("../../workspace/ecosystem-template");
    expect(ECOSYSTEM_REUSE_MATRIX.authentication.beauty).toBe(true);
    expect(ECOSYSTEM_REUSE_MATRIX.mission_control.automotive).toBe(true);
    expect(moduleRegistry.get("beauty")?.apiHint).toContain("enterprise-bos");
    expect(applicationRegistry.get("beauty_enterprise")?.route).toBe("/workspace/beauty");
  });

  it("routes beauty in role journeys", async () => {
    const { PILOT_ROLE_JOURNEYS } = await import("../pilot/roleJourneys");
    expect(PILOT_ROLE_JOURNEYS.every((j) => j.steps.some((s) => s.route.includes("beauty")))).toBe(
      true,
    );
    const { assignModule } = await import("@/integrations/pilotFeedback");
    expect(assignModule("salon appointment failed", "beauty")).toBe("beauty");
  });
});

describe("Sprint 30.9 Beauty Pilot Execution", () => {
  it("computes full platform reuse and wires commerce", async () => {
    expect(webConfig.commerceCorePrefix).toContain("enterprise-eco");
    expect(hubIntegrations.commerceCore).toContain("enterprise-eco");
    const { computeReusePercentage, stepAiTeamConfigure } = await import(
      "../../workspace/ecosystem-template"
    );
    expect(typeof stepAiTeamConfigure).toBe("function");
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.sharedCount).toBe(audit.totalCount);
    expect(audit.totalCount).toBeGreaterThanOrEqual(16);
  });
});
