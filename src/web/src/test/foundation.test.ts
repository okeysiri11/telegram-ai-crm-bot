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
    expect(webConfig.sprint).toBe("32.0");
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
    expect(hubIntegrations.pilotReadiness).toContain("enterprise-epr");
    expect(hubIntegrations.productionReadiness).toContain("enterprise-epd");
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
    expect(moduleRegistry.get("pilot")?.routes).toContain("/pilot/production");
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

describe("Sprint 31.0 Cafe Pilot Execution", () => {
  it("wires cafe prefix and cross-ecosystem reuse", async () => {
    expect(webConfig.cafeOsPrefix).toContain("enterprise-cos");
    expect(hubIntegrations.cafeOs).toContain("enterprise-cos");
    const { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } = await import(
      "../../workspace/ecosystem-template"
    );
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.dimensions.every((d) => "cafe" in d)).toBe(true);
    expect(CROSS_ECOSYSTEM_PATTERNS.length).toBeGreaterThan(3);
    expect(moduleRegistry.get("cafe")?.apiHint).toContain("enterprise-cos");
    expect(applicationRegistry.get("cafe_enterprise")?.route).toBe("/workspace/cafe");
  });
});

describe("Sprint 31.1 Agriculture Pilot Execution", () => {
  it("wires agro prefixes and four-ecosystem reuse", async () => {
    expect(webConfig.agroPrefix).toContain("/api/agro/v1");
    expect(webConfig.agroSupplyChainPrefix).toContain("agro-supply-chain");
    expect(hubIntegrations.agro).toContain("/api/agro/v1");
    expect(hubIntegrations.aiAgronomist).toContain("ai-agronomist");
    const { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } = await import(
      "../../workspace/ecosystem-template"
    );
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.dimensions.every((d) => "agriculture" in d)).toBe(true);
    expect(CROSS_ECOSYSTEM_PATTERNS.some((p) => /Agriculture/i.test(p))).toBe(true);
    expect(moduleRegistry.get("agro")?.apiHint).toContain("/api/agro/v1");
    expect(applicationRegistry.get("agro_enterprise")?.route).toBe("/workspace/agro");
  });
});

describe("Sprint 31.2 Legal Pilot Execution", () => {
  it("wires legal prefixes and five-ecosystem reuse", async () => {
    expect(webConfig.legalEnterprisePrefix).toContain("legal-enterprise");
    expect(webConfig.legalCasePrefix).toContain("legal-cm");
    expect(webConfig.legalDocumentsPrefix).toContain("legal-di");
    expect(hubIntegrations.legalCase).toContain("legal-cm");
    expect(hubIntegrations.legalAi).toContain("legal-aa");
    const { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } = await import(
      "../../workspace/ecosystem-template"
    );
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.dimensions.every((d) => "legal" in d)).toBe(true);
    expect(CROSS_ECOSYSTEM_PATTERNS.some((p) => /Legal/i.test(p))).toBe(true);
    expect(moduleRegistry.get("legal")?.apiHint).toContain("legal-cm");
    expect(applicationRegistry.get("legal_enterprise")?.route).toBe("/workspace/legal");
  });
});

describe("Sprint 31.3 Bidex Pilot Execution", () => {
  it("wires bidex finance prefixes and six-ecosystem reuse", async () => {
    expect(webConfig.financeDigitalAssetsPrefix).toContain("finance-da");
    expect(webConfig.cryptoEnterprisePrefix).toContain("crypto-enterprise");
    expect(hubIntegrations.financeDigitalAssets).toContain("finance-da");
    expect(hubIntegrations.cryptoRisk).toContain("crypto-rm");
    const { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } = await import(
      "../../workspace/ecosystem-template"
    );
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.dimensions.every((d) => "crypto" in d)).toBe(true);
    expect(CROSS_ECOSYSTEM_PATTERNS.some((p) => /Bidex/i.test(p))).toBe(true);
    expect(moduleRegistry.get("crypto")?.apiHint).toContain("finance-da");
    expect(applicationRegistry.get("crypto_enterprise")?.route).toBe("/workspace/crypto");
  });
});

describe("Sprint 31.4 Drone Ecosystem Completion", () => {
  it("wires drone prefixes and seven-ecosystem reuse", async () => {
    expect(webConfig.dronePrefix).toContain("/api/drone/v1");
    expect(webConfig.precisionAgriculturePrefix).toContain("precision-agriculture");
    expect(hubIntegrations.drone).toContain("/api/drone/v1");
    expect(hubIntegrations.precisionAgriculture).toContain("precision-agriculture");
    const { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } = await import(
      "../../workspace/ecosystem-template"
    );
    const audit = computeReusePercentage();
    expect(audit.reusePercent).toBe(100);
    expect(audit.dimensions.every((d) => "drone" in d)).toBe(true);
    expect(CROSS_ECOSYSTEM_PATTERNS.some((p) => /Drone/i.test(p))).toBe(true);
    expect(moduleRegistry.get("drone")?.apiHint).toContain("/api/drone/v1");
    expect(applicationRegistry.get("drone_enterprise")?.route).toBe("/workspace/drone");
  });
});

describe("Sprint 32.0 Enterprise Web Completion", () => {
  it("exposes production readiness audit and score", async () => {
    const {
      WORKSPACE_HEALTH_PROBES,
      PLATFORM_HEALTH_PROBES,
      PRODUCTION_CHECKLIST,
      productionReadinessScore,
      webCompletionSummary,
    } = await import("../pilot/webCompletionAudit");
    expect(WORKSPACE_HEALTH_PROBES).toHaveLength(7);
    expect(WORKSPACE_HEALTH_PROBES.map((w) => w.route)).toEqual([
      "/workspace/auto",
      "/workspace/beauty",
      "/workspace/cafe",
      "/workspace/agro",
      "/workspace/legal",
      "/workspace/crypto",
      "/workspace/drone",
    ]);
    expect(PLATFORM_HEALTH_PROBES.length).toBeGreaterThanOrEqual(5);
    expect(PRODUCTION_CHECKLIST.some((c) => c.id === "auth" && c.status === "ready")).toBe(true);
    expect(productionReadinessScore()).toBeGreaterThanOrEqual(75);
    expect(webCompletionSummary().ecosystems).toBe(7);
    expect(applicationRegistry.get("production_readiness")?.route).toBe("/pilot/production");
  });
});
