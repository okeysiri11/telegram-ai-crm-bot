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
    expect(webConfig.sprint).toBe("32.3.4");
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
    expect(hubIntegrations.tenancy).toContain("enterprise-tenancy");
    expect(hubIntegrations.onboarding).toContain("enterprise-eon");
    expect(hubIntegrations.ecosystem).toContain("/api/ecosystem/v1");
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
    expect(moduleRegistry.get("pilot")?.routes).toContain("/pilot/onboard");
    expect(moduleRegistry.get("pilot")?.routes).toContain("/pilot/invite");
    expect(moduleRegistry.get("pilot")?.routes).toContain("/pilot/execute");
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

describe("Sprint 32.1 External Pilot Hardening", () => {
  it("exposes onboarding, invitations, and elevated readiness score", async () => {
    const {
      PRODUCTION_CHECKLIST,
      IDENTITY_HARDENING_CHECKLIST,
      PILOT_OPS_STEPS,
      productionReadinessScore,
      identityHardeningScore,
    } = await import("../pilot/webCompletionAudit");
    expect(PRODUCTION_CHECKLIST.some((c) => c.id === "pilot_invite" && c.status === "ready")).toBe(true);
    expect(PRODUCTION_CHECKLIST.some((c) => c.id === "tenant_onboard" && c.status === "ready")).toBe(true);
    expect(productionReadinessScore()).toBeGreaterThanOrEqual(90);
    expect(identityHardeningScore()).toBeGreaterThanOrEqual(80);
    expect(IDENTITY_HARDENING_CHECKLIST.some((c) => c.id === "invite_tokens")).toBe(true);
    expect(PILOT_OPS_STEPS.some((s) => s.route === "/pilot/onboard")).toBe(true);
    expect(applicationRegistry.get("external_pilot_onboard")?.route).toBe("/pilot/onboard");
    expect(applicationRegistry.get("pilot_invite")?.route).toBe("/pilot/invite");
  });
});

describe("Sprint 32.2 Pilot Execution", () => {
  it("exposes execution route, metrics, and feedback backlog helpers", async () => {
    const { PILOT_OPS_STEPS } = await import("../pilot/webCompletionAudit");
    expect(PILOT_OPS_STEPS.some((s) => s.route === "/pilot/execute")).toBe(true);
    expect(applicationRegistry.get("pilot_execution")?.route).toBe("/pilot/execute");
    const { pilotMetrics } = await import("@/integrations/pilotMetrics");
    expect(typeof pilotMetrics.recordOnboarding).toBe("function");
    expect(typeof pilotMetrics.recordInvitation).toBe("function");
    const { FEEDBACK_MODULE_CHECKLIST, feedbackBacklogSummary, assignModule } = await import(
      "@/integrations/pilotFeedback"
    );
    expect(FEEDBACK_MODULE_CHECKLIST.length).toBeGreaterThanOrEqual(7);
    expect(assignModule("salon appointment failed", "beauty")).toBe("beauty");
    expect(feedbackBacklogSummary().total).toBeGreaterThanOrEqual(0);
    const { PILOT_ROLE_JOURNEYS } = await import("../pilot/roleJourneys");
    expect(PILOT_ROLE_JOURNEYS[0].steps.some((s) => s.route === "/pilot/execute")).toBe(true);
  });
});

describe("Sprint 32.3.1 First User Experience", () => {
  it("exposes extensible role catalog and first-entry progress helpers", async () => {
    const { firstEntryRoleCatalog, FIRST_ENTRY_STEPS } = await import("../onboarding/firstEntryRoles");
    expect(FIRST_ENTRY_STEPS).toHaveLength(7);
    expect(firstEntryRoleCatalog.list().length).toBeGreaterThanOrEqual(8);
    firstEntryRoleCatalog.register({
      id: "test_ext_role",
      label: "Ext Role",
      description: "Extension point",
      icon: "XX",
    });
    expect(firstEntryRoleCatalog.get("test_ext_role")?.label).toBe("Ext Role");
    const { isFirstEntryComplete, resetFirstEntry, markFirstEntryComplete, saveFirstEntry } =
      await import("../onboarding/firstEntryStore");
    resetFirstEntry();
    expect(isFirstEntryComplete()).toBe(false);
    saveFirstEntry({ roleId: "beauty_salon", companyName: "Demo" });
    markFirstEntryComplete();
    expect(isFirstEntryComplete()).toBe(true);
    resetFirstEntry();
  });
});

describe("Sprint 32.3.2 Enterprise Command Center", () => {
  it("exposes layout catalog and default sections", async () => {
    const {
      DEFAULT_COMMAND_LAYOUT,
      QUICK_ACTIONS,
      BUSINESS_MODULES,
      KPI_CARDS,
      loadCommandLayout,
      saveCommandLayout,
      toggleCommandSection,
    } = await import("../dashboard/commandCenterCatalog");
    expect(DEFAULT_COMMAND_LAYOUT).toContain("mission_control");
    expect(QUICK_ACTIONS.length).toBeGreaterThanOrEqual(6);
    expect(BUSINESS_MODULES.some((m) => m.id === "crm")).toBe(true);
    expect(KPI_CARDS).toHaveLength(6);
    saveCommandLayout([...DEFAULT_COMMAND_LAYOUT]);
    const without = toggleCommandSection("ai_activity");
    expect(without).not.toContain("ai_activity");
    const restored = toggleCommandSection("ai_activity");
    expect(restored).toContain("ai_activity");
    const loaded = loadCommandLayout();
    expect(loaded).toContain("activity_feed");
    saveCommandLayout([...DEFAULT_COMMAND_LAYOUT]);
  });
});

describe("Sprint 32.3.3 Enterprise City", () => {
  it("maps buildings to existing routes and supports search", async () => {
    const { CITY_BUILDINGS, searchBuildings, getBuilding } = await import("../enterprise-city/cityCatalog");
    expect(CITY_BUILDINGS.length).toBeGreaterThanOrEqual(12);
    expect(getBuilding("crm")?.route).toBe("/workspace/crm");
    expect(getBuilding("ai_team")?.route).toBe("/platform-builder/ai-team");
    expect(getBuilding("dashboard")?.route).toBe("/dashboard");
    expect(searchBuildings("finance").some((b) => b.id === "finance")).toBe(true);
    expect(CITY_BUILDINGS.every((b) => b.route.startsWith("/"))).toBe(true);
  });
});

describe("Sprint 32.3.4 Live Enterprise", () => {
  it("exposes health probes and seed activity catalog", async () => {
    const { ENTERPRISE_HEALTH_PROBES, SEED_ACTIVITY, LIVE_POLL_MS } = await import("../live-ops/liveEnterpriseCatalog");
    expect(ENTERPRISE_HEALTH_PROBES.length).toBeGreaterThanOrEqual(6);
    expect(SEED_ACTIVITY.some((a) => a.kind === "ai")).toBe(true);
    expect(LIVE_POLL_MS).toBeGreaterThanOrEqual(10_000);
    const { emptyLiveSnapshot } = await import("../live-ops/fetchLiveEnterprise");
    const snap = emptyLiveSnapshot();
    expect(snap.timeline).toHaveLength(4);
    expect(snap.recommendations.length).toBeGreaterThan(0);
  });
});
