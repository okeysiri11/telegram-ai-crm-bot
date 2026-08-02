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
    expect(webConfig.version).toBe("9.5.0");
    expect(webConfig.sprint).toBe("33.1");
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
    expect(DEFAULT_COMMAND_LAYOUT).toContain("enterprise_health");
    expect(DEFAULT_COMMAND_LAYOUT).toContain("quick_actions");
    expect(DEFAULT_COMMAND_LAYOUT).toContain("business_kpi");
    expect(QUICK_ACTIONS.length).toBeGreaterThanOrEqual(6);
    expect(BUSINESS_MODULES.some((m) => m.id === "crm")).toBe(true);
    expect(KPI_CARDS.length).toBeGreaterThanOrEqual(5);
    const saved = saveCommandLayout(["mission_control", "quick_actions"]);
    expect(loadCommandLayout()).toEqual(saved);
    const toggled = toggleCommandSection("ai_activity");
    expect(toggled).toContain("ai_activity");
    saveCommandLayout([...DEFAULT_COMMAND_LAYOUT]);
  });
});

describe("EP-01 CEO Morning Brief", () => {
  it("derives five executive answers from live snapshot", async () => {
    const { emptyLiveSnapshot } = await import("../live-ops/fetchLiveEnterprise");
    const { deriveMorningBrief } = await import("../dashboard/deriveMorningBrief");
    const brief = deriveMorningBrief(emptyLiveSnapshot(), {
      company: "Demo Corp",
      unread: 2,
      conciergeName: "Nora",
    });
    expect(brief.company).toBe("Demo Corp");
    expect(brief.happening.length).toBeGreaterThan(0);
    expect(brief.attention.length).toBeGreaterThan(0);
    expect(brief.aiActions.length).toBeGreaterThan(0);
    expect(brief.risks.length).toBeGreaterThan(0);
    expect(brief.opportunities.length).toBeGreaterThan(0);
    expect(["calm", "watch", "alert"]).toContain(brief.tone);
    expect(brief.aiActions.every((a) => a.impact)).toBe(true);
    expect(brief.greeting).toMatch(/Good (morning|afternoon|evening)/);
  });
});

describe("EP-06 Decision Flow", () => {
  it("resolves continue chain and CEO primary action", async () => {
    const {
      DECISION_FLOW_VERSION,
      DECISION_CHAIN,
      resolveContinue,
      deriveCeoPrimaryAction,
      withDecisionQuery,
      CROSS_MODULE_FLOW,
    } = await import("../decision-flow");
    expect(DECISION_FLOW_VERSION).toBe("1.0");
    expect(DECISION_CHAIN.length).toBe(6);
    expect(CROSS_MODULE_FLOW["/dashboard"].cta).toMatch(/Control Tower/i);
    const cont = resolveContinue("/dashboard");
    expect(cont?.cta).toBeTruthy();
    expect(withDecisionQuery("/workspace/crm", { from: "/dashboard", step: "act" })).toContain("from=");
    const primary = deriveCeoPrimaryAction({ tone: "alert", unread: 0, healthBad: true });
    expect(primary.cta).toMatch(/Attention|Resolve/i);
  });
});

describe("EP-07 Production Excellence", () => {
  it("exposes production helpers and hardened live poll interval", async () => {
    const { PRODUCTION_EXCELLENCE_VERSION, sanitizeErrorMessage, reliabilityCopy, LIVE_FETCH_DEDUPE_MS } =
      await import("../production");
    const { LIVE_POLL_MS } = await import("../live-ops/liveEnterpriseCatalog");
    const { LAUNCH_READINESS } = await import("../launch/launchCatalog");
    expect(PRODUCTION_EXCELLENCE_VERSION).toBe("1.0");
    expect(LIVE_POLL_MS).toBeGreaterThanOrEqual(20_000);
    expect(LIVE_FETCH_DEDUPE_MS).toBeGreaterThanOrEqual(2_500);
    expect(sanitizeErrorMessage("Bearer abc.def.ghi leaked")).toContain("[redacted]");
    expect(reliabilityCopy("offline").action).toBeTruthy();
    expect(LAUNCH_READINESS.performance.singletonLivePoller).toBe(true);
    expect(LAUNCH_READINESS.score).toBeGreaterThanOrEqual(94);
    expect(LAUNCH_READINESS.gaCertified).toBe(true);
  });
});

describe("Sprint 1.1.1 GA Audit Corrections", () => {
  it(
    "exposes governance edge, audit vault foundation, and route boundary module",
    async () => {
      const { evaluateGovernanceEdge, GOVERNANCE_EDGE_MIGRATION } = await import("../enterprise-governance");
      const { AUDIT_VAULT_FOUNDATION, appendAuditVault } = await import("../audit-vault");
      const { RouteErrorBoundary } = await import("../shell/RouteErrorBoundary");
      const edge = await evaluateGovernanceEdge({ action: "read.dashboard", roleId: "owner" });
      expect(edge.decision).toBe("allow");
      expect(GOVERNANCE_EDGE_MIGRATION.version).toBe("1.1.1");
      expect(AUDIT_VAULT_FOUNDATION.status).toBe("foundation_only");
      const rec = await appendAuditVault({ actor: "test", action: "smoke" });
      expect(rec.immutable).toBe(false);
      expect(RouteErrorBoundary).toBeTruthy();
    },
    15_000,
  );
});

describe("Sprint 32.3.3 Enterprise City", () => {
  it("maps buildings to existing routes and supports search", async () => {
    const { CITY_BUILDINGS, searchBuildings, getBuilding } = await import("../enterprise-city/cityCatalog");
    expect(CITY_BUILDINGS.length).toBeGreaterThanOrEqual(12);
    expect(getBuilding("crm")?.route).toBe("/crm");
    expect(getBuilding("ai_team")?.route).toBe("/ai-agents");
    expect(getBuilding("dashboard")?.route).toBe("/dashboard");
    expect(searchBuildings("finance").some((b) => b.id === "finance")).toBe(true);
    expect(CITY_BUILDINGS.every((b) => b.route.startsWith("/"))).toBe(true);
  });

  it("exposes EP-05 visual state language and identity", async () => {
    const {
      CITY_EXPERIENCE_VERSION,
      CITY_STATE_LABELS,
      resolveVisualState,
      buildingIdentity,
      cityGlance,
    } = await import("../enterprise-city/cityVisualLanguage");
    const { CITY_STATUS_SEED } = await import("../enterprise-city/cityCatalog");
    expect(CITY_EXPERIENCE_VERSION).toMatch(/^1\./);
    expect(CITY_STATE_LABELS.critical.ru).toBe("Критично");
    expect(CITY_STATE_LABELS.ok.ua).toBeTruthy();
    expect(resolveVisualState(CITY_STATUS_SEED.crm)).toBeTruthy();
    expect(buildingIdentity("crm").silhouette).toContain("ec-sil");
    const glance = cityGlance(CITY_STATUS_SEED);
    expect(glance.total).toBeGreaterThanOrEqual(12);
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

describe("Sprint 32.3.5 Enterprise Demo Polish", () => {
  it("resolves executive mode and demo scenario steps", async () => {
    const { resolveExecutiveMode, EXECUTIVE_LAYOUT, isExecutiveRole } = await import("../demo/executiveMode");
    expect(isExecutiveRole("executive")).toBe(true);
    expect(isExecutiveRole("client")).toBe(false);
    expect(resolveExecutiveMode({ queryMode: "executive" })).toBe(true);
    expect(resolveExecutiveMode({ queryMode: "full", roleId: "executive" })).toBe(false);
    expect(EXECUTIVE_LAYOUT).toContain("business_kpi");
    expect(EXECUTIVE_LAYOUT).toContain("quick_actions");
    expect(EXECUTIVE_LAYOUT).toContain("mission_control");
    expect(EXECUTIVE_LAYOUT).toContain("enterprise_health");
    const { DEMO_SCENARIO_STEPS } = await import("../demo/demoScenarioCatalog");
    expect(DEMO_SCENARIO_STEPS.length).toBeGreaterThanOrEqual(8);
    expect(DEMO_SCENARIO_STEPS.some((s) => s.route.includes("/dashboard"))).toBe(true);
    const { SHARED_UI } = await import("../ui/sharedUi");
    expect(SHARED_UI.loaders).toContain("Skeleton");
  });
});

describe("Sprint 32.3.6 Unified Workspace", () => {
  it("exposes quick switch routes and breadcrumb labels", async () => {
    const { GLOBAL_QUICK_SWITCH, labelForSegment, detectActiveEcosystem } = await import(
      "../workspace-chrome/workspaceContext"
    );
    expect(GLOBAL_QUICK_SWITCH.length).toBeGreaterThanOrEqual(8);
    expect(GLOBAL_QUICK_SWITCH.some((i) => i.route === "/dashboard")).toBe(true);
    expect(labelForSegment("crm")).toBe("CRM");
    expect(labelForSegment("beauty")).toBe("Бьюти");
    expect(detectActiveEcosystem("/workspace/beauty/crm")).toBe("Бьюти");
    const { breadcrumbEngine } = await import("../../navigation/managers/breadcrumbEngine");
    const crumbs = breadcrumbEngine.fromPath("/workspace/beauty/crm");
    expect(crumbs[0]?.label).toBe("Главная");
    expect(crumbs.some((c) => c.label === "Бьюти")).toBe(true);
  });
});

describe("Sprint 32.3.7 Launch Validation", () => {
  it("exposes demo steps and readiness score", async () => {
    const { LAUNCH_DEMO_STEPS, LAUNCH_CRITICAL_ROUTES, LAUNCH_READINESS } = await import("../launch/launchCatalog");
    expect(LAUNCH_DEMO_STEPS.length).toBeGreaterThanOrEqual(10);
    expect(LAUNCH_DEMO_STEPS.some((s) => s.route === "/dashboard")).toBe(true);
    expect(LAUNCH_CRITICAL_ROUTES).toContain("/enterprise-city");
    expect(LAUNCH_CRITICAL_ROUTES).toContain("/platform-builder/knowledge");
    expect(LAUNCH_READINESS.score).toBeGreaterThanOrEqual(90);
    expect(LAUNCH_READINESS.commercial.demoScenarioGaPath).toBe(true);
  });
});

describe("Sprint 32.4 AI Operating System", () => {
  it("provides path-aware suggestions and chrome exports", async () => {
    const { suggestionsForPath, sectionKeyFromPath } = await import("../ai-os-chrome/smartSuggestions");
    expect(sectionKeyFromPath("/workspace/crm")).toBe("crm");
    expect(sectionKeyFromPath("/enterprise-city")).toBe("city");
    expect(sectionKeyFromPath("/platform-builder/knowledge")).toBe("knowledge");
    const crm = suggestionsForPath("/workspace/crm", 5);
    expect(crm.length).toBeGreaterThanOrEqual(2);
    expect(crm.length).toBeLessThanOrEqual(5);
    expect(crm.some((s) => s.id === "crm_create")).toBe(true);
    expect(crm[0].observation).toBeTruthy();
    expect(crm[0].impact).toBeTruthy();
    expect(crm[0].confidence).toBeTruthy();
    const finance = suggestionsForPath("/workspace/finance", 5);
    expect(finance.length).toBeGreaterThanOrEqual(2);
    const { AiOsExperienceChrome, AI_PERSONALITY_VERSION, advisorContextLine } = await import("../ai-os-chrome");
    expect(typeof AiOsExperienceChrome).toBe("function");
    expect(AI_PERSONALITY_VERSION).toBe("1.0");
    expect(advisorContextLine({ section: "dashboard", company: "Acme", healthOk: 3, healthTotal: 3, unread: 0, aiBusy: false })).toMatch(/Acme/);
  });
});

describe("Sprint 32.5 Enterprise Intelligence", () => {
  it("derives brief, priorities, and cross-module links from snapshot", async () => {
    const { deriveIntelligence } = await import("../enterprise-intelligence/deriveIntelligence");
    const { emptyLiveSnapshot } = await import("../live-ops/fetchLiveEnterprise");
    const snap = {
      ...emptyLiveSnapshot(),
      activity: [
        {
          id: "a1",
          kind: "task" as const,
          title: "CRM клиент требует внимания",
          detail: "deal overdue",
          at: new Date().toISOString(),
          source: "seed" as const,
          moduleHint: "crm",
        },
      ],
      recommendations: [
        { id: "r1", title: "Risk on pipeline", tone: "risk" as const },
        { id: "r2", title: "Improve knowledge docs", tone: "improve" as const },
      ],
      aiOps: {
        running: [],
        queue: ["sync leads"],
        recent: ["auto email"],
        status: "ok",
        errors: [],
        completed: ["auto email", "score leads"],
      },
      health: [
        { id: "knowledge" as const, label: "Knowledge Base", ok: true, detail: "ok" },
        { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
      ],
      activeModules: ["crm", "knowledge"],
      mcOk: true,
    };
    const intel = deriveIntelligence(snap, [
      {
        id: "n1",
        kind: "ai",
        title: "AI insight",
        body: "client attention",
        createdAt: new Date().toISOString(),
        read: false,
      },
    ]);
    expect(intel.brief.bullets.length).toBeGreaterThanOrEqual(3);
    expect(intel.insights.some((i) => i.category === "risk")).toBe(true);
    expect(intel.priorities.some((p) => p.bucket === "urgent")).toBe(true);
    expect(intel.crossModule.some((c) => c.from === "crm")).toBe(true);
    expect(intel.knowledgeAware).toBe(true);
    expect(intel.decision.decideToday.length).toBeGreaterThanOrEqual(1);
    const { suggestionsForPath } = await import("../ai-os-chrome/smartSuggestions");
    const sug = suggestionsForPath("/dashboard", 5, snap);
    expect(sug.some((s) => s.id === "kb_aware")).toBe(true);
  });
});

describe("Sprint 32.6 AI Team Collaboration", () => {
  it("derives multi-agent workspace from live snapshot", async () => {
    const { deriveTeamCollaboration } = await import("../ai-team-collaboration/deriveTeamCollaboration");
    const { emptyLiveSnapshot } = await import("../live-ops/fetchLiveEnterprise");
    const snap = {
      ...emptyLiveSnapshot(),
      aiOps: {
        running: ["Sales Specialist", "Marketing Specialist"],
        queue: ["Review CRM brief", "Campaign draft"],
        recent: ["Подготовлен brief по сделкам"],
        status: "operational",
        errors: [],
        completed: ["Follow-up · 12", "Feedback · 8"],
      },
      activity: [
        {
          id: "a1",
          kind: "document" as const,
          title: "AI создал документ",
          detail: "Knowledge",
          at: new Date().toISOString(),
          source: "seed" as const,
          moduleHint: "knowledge",
        },
      ],
    };
    const bundle = deriveTeamCollaboration(snap, {
      conciergeName: "Nova",
      notifications: [
        {
          id: "n1",
          kind: "ai",
          title: "Team update",
          body: "ready",
          createdAt: new Date().toISOString(),
          read: false,
        },
      ],
    });
    expect(bundle.members.some((m) => m.isConcierge)).toBe(true);
    expect(bundle.members.length).toBeGreaterThanOrEqual(3);
    expect(bundle.distribution.length).toBeGreaterThanOrEqual(2);
    expect(bundle.timeline[0]?.label).toBe("Concierge");
    expect(bundle.timeline.at(-1)?.label).toBe("Result");
    expect(bundle.health.activeCount).toBeGreaterThanOrEqual(1);
    expect(bundle.conversation.length).toBeGreaterThanOrEqual(3);
    expect(bundle.knowledge.length).toBeGreaterThanOrEqual(1);
    expect(bundle.overview.summaryLines.length).toBe(4);
  });
});

describe("Sprint 32.7 Enterprise Workflow Automation", () => {
  it("derives workflow runs and templates with city paths", async () => {
    const { deriveWorkflowAutomation } = await import("../enterprise-workflow/deriveWorkflowAutomation");
    const { BUSINESS_WORKFLOW_TEMPLATES } = await import("../enterprise-workflow/workflowTemplates");
    const { emptyLiveSnapshot } = await import("../live-ops/fetchLiveEnterprise");
    expect(BUSINESS_WORKFLOW_TEMPLATES.some((t) => t.libraryLabel === "Новый клиент")).toBe(true);
    expect(BUSINESS_WORKFLOW_TEMPLATES.some((t) => t.id === "contract")).toBe(true);
    const snap = {
      ...emptyLiveSnapshot(),
      aiOps: {
        running: ["Sales Specialist"],
        queue: ["Review CRM brief"],
        recent: ["Подготовлен brief"],
        status: "operational",
        errors: ["timeout"],
        completed: ["Follow-up · 12", "Feedback · 8"],
      },
      activity: [
        {
          id: "a1",
          kind: "automation" as const,
          title: "Новый клиент создан",
          detail: "CRM",
          at: new Date().toISOString(),
          source: "seed" as const,
          moduleHint: "crm",
        },
      ],
      activeModules: ["crm", "sales"],
    };
    const bundle = deriveWorkflowAutomation(snap, [], "new_client");
    expect(bundle.active.length).toBeGreaterThanOrEqual(1);
    expect(bundle.completed.length).toBeGreaterThanOrEqual(1);
    expect(bundle.errors.length).toBeGreaterThanOrEqual(1);
    expect(bundle.monitor?.steps[0]?.label).toBeTruthy();
    expect(bundle.cityRoute.length).toBeGreaterThanOrEqual(2);
    expect(bundle.metrics.timeSavedMin).toBeGreaterThan(0);
    expect(bundle.templates.length).toBeGreaterThanOrEqual(5);
  });
});

describe("Sprint 32.8 AI Builder Studio", () => {
  it("exposes studio catalogs and home cards", async () => {
    const {
      STUDIO_HOME_CARDS,
      DOMAIN_SKILL_PACKS,
      PROMPT_LIBRARY,
      ECOSYSTEM_TEMPLATES,
      studioCatalogStats,
    } = await import("../ai-builder-studio/studioCatalog");
    expect(STUDIO_HOME_CARDS.some((c) => c.title === "AI Team")).toBe(true);
    expect(STUDIO_HOME_CARDS.some((c) => c.title === "Prompt Library")).toBe(true);
    expect(DOMAIN_SKILL_PACKS.map((p) => p.title)).toEqual(
      expect.arrayContaining(["CRM", "Marketing", "Sales", "Legal", "Analytics", "Finance", "Knowledge", "Automation"]),
    );
    expect(PROMPT_LIBRARY.some((p) => p.kind === "system")).toBe(true);
    expect(PROMPT_LIBRARY.some((p) => p.kind === "corporate")).toBe(true);
    expect(ECOSYSTEM_TEMPLATES).toHaveLength(7);
    expect(ECOSYSTEM_TEMPLATES.map((t) => t.title)).toEqual(
      expect.arrayContaining(["Beauty", "Legal", "Cafe", "Automotive", "Agriculture", "Drone", "Bidex"]),
    );
    const stats = studioCatalogStats();
    expect(stats.skills).toBeGreaterThan(5);
    expect(stats.prompts).toBeGreaterThan(5);
    expect(stats.templates).toBe(7);
    const { AIBuilderStudioPage } = await import("../ai-builder-studio");
    expect(typeof AIBuilderStudioPage).toBe("function");
  });
});

describe("Sprint 32.9 Enterprise Marketplace", () => {
  it("lists solutions, packs, and compatibility checks", async () => {
    const {
      MARKETPLACE_SOLUTIONS,
      MARKETPLACE_CATEGORIES,
      getMarketplaceSolution,
    } = await import("../enterprise-marketplace/solutionCatalog");
    const { checkCompatibility, installSolution, resolveStatus } = await import(
      "../enterprise-marketplace/installState"
    );
    expect(MARKETPLACE_CATEGORIES.some((c) => c.id === "ai_teams")).toBe(true);
    expect(MARKETPLACE_CATEGORIES.some((c) => c.id === "enterprise_hub")).toBe(true);
    const packs = MARKETPLACE_SOLUTIONS.filter((s) => s.enterprisePack);
    expect(packs).toHaveLength(7);
    expect(packs.map((p) => p.title)).toEqual(
      expect.arrayContaining([
        "Beauty Enterprise Pack",
        "Legal Enterprise Pack",
        "Cafe Enterprise Pack",
        "Agriculture Enterprise Pack",
        "Automotive Enterprise Pack",
        "Drone Enterprise Pack",
        "Bidex Enterprise Pack",
      ]),
    );
    const sol = getMarketplaceSolution("team_sales_ops");
    expect(sol).toBeTruthy();
    const report = checkCompatibility(sol!, {
      workspaceId: "ws_demo",
      ecosystem: "platform",
      roleId: "owner",
      hasAccess: true,
      platformVersion: "9.4.0",
    });
    expect(report.ok).toBe(true);
    const rec = installSolution(sol!);
    expect(rec.imported.team).toBe(true);
    expect(resolveStatus(sol!)).toBe("installed");
  });
});

describe("Sprint 33.0 Enterprise Digital Twin", () => {
  it("derives org map, graph, heatmap, impact, timeline", async () => {
    const { deriveEnterpriseTwin, RELATIONSHIP_CHAIN } = await import("../enterprise-twin/deriveTwin");
    const { SEED_ACTIVITY } = await import("../live-ops/liveEnterpriseCatalog");
    const snapshot = {
      updatedAt: new Date().toISOString(),
      activity: SEED_ACTIVITY,
      aiOps: {
        running: ["Sales Ops"],
        queue: ["Queue A"],
        recent: ["Brief ready"],
        status: "ok",
        errors: [],
        completed: ["Lead intake"],
      },
      timeline: [],
      health: [
        { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
        { id: "knowledge" as const, label: "Knowledge", ok: true, detail: "ok" },
        { id: "mission_control" as const, label: "MC", ok: true, detail: "ok" },
      ],
      recommendations: [],
      mcOk: true,
      activeModules: ["crm", "ai", "beauty"],
    };
    const twin = deriveEnterpriseTwin(snapshot, {
      company: "Demo Corp",
      notifications: [{ id: "1", kind: "task" as const, title: "T", body: "b", createdAt: "", read: false }],
      roleId: "owner",
    });
    expect(RELATIONSHIP_CHAIN.map((s) => s.id)).toEqual([
      "clients",
      "crm",
      "sales",
      "documents",
      "finance",
      "knowledge",
      "ai_team",
    ]);
    expect(twin.nodes.length).toBeGreaterThan(10);
    expect(twin.nodes.some((n) => n.kind === "ecosystem")).toBe(true);
    expect(twin.heatmap.length).toBeGreaterThan(0);
    expect(twin.executive.happening.length).toBeGreaterThan(0);
    expect(twin.timeline.length).toBeGreaterThan(0);
    expect(twin.impacts.ai_team?.effects.length).toBeGreaterThan(0);
    expect(twin.graph.length).toBe(RELATIONSHIP_CHAIN.length - 1);
  });
});

describe("Sprint 33.1 Enterprise Integration Hub", () => {
  it("lists communication, business, developer integrations and derives dashboard", async () => {
    const {
      ALL_INTEGRATIONS,
      COMMUNICATION_INTEGRATIONS,
      BUSINESS_INTEGRATIONS,
      DEVELOPER_INTEGRATIONS,
    } = await import("../enterprise-integrations/integrationCatalog");
    const { deriveIntegrationHub } = await import("../enterprise-integrations/deriveIntegrations");
    const { connectIntegration, resolveStatus } = await import("../enterprise-integrations/connectionState");

    expect(COMMUNICATION_INTEGRATIONS.map((i) => i.id)).toEqual(
      expect.arrayContaining(["telegram", "whatsapp", "email", "sms", "web_widget", "push"]),
    );
    expect(BUSINESS_INTEGRATIONS.map((i) => i.id)).toEqual(
      expect.arrayContaining(["crm", "erp", "accounting", "payments", "documents", "calendar", "storage"]),
    );
    expect(DEVELOPER_INTEGRATIONS.map((i) => i.id)).toEqual(
      expect.arrayContaining(["rest_api", "webhooks", "oauth", "api_keys", "sdk"]),
    );
    expect(ALL_INTEGRATIONS.length).toBe(
      COMMUNICATION_INTEGRATIONS.length + BUSINESS_INTEGRATIONS.length + DEVELOPER_INTEGRATIONS.length,
    );

    const bundle = deriveIntegrationHub({
      updatedAt: new Date().toISOString(),
      activity: [],
      aiOps: { running: [], queue: [], recent: [], status: "ok", errors: [], completed: [] },
      timeline: [],
      health: [{ id: "crm" as const, label: "CRM", ok: true, detail: "ok" }],
      recommendations: [],
      mcOk: true,
      activeModules: ["crm"],
    });
    expect(bundle.dashboard.active).toBeGreaterThan(0);
    expect(bundle.rows.length).toBe(ALL_INTEGRATIONS.length);
    expect(bundle.twin.connectedSystems.length).toBeGreaterThan(0);

    connectIntegration("whatsapp");
    expect(resolveStatus("whatsapp")).toBe("active");
  });
});

describe("Sprint 33.2 AI Runtime & Orchestration", () => {
  it("derives jobs, queue, orchestration, health from aiOps", async () => {
    const { deriveRuntime, ORCH_CHAIN } = await import("../ai-runtime/deriveRuntime");
    const snapshot = {
      updatedAt: new Date().toISOString(),
      activity: [],
      aiOps: {
        running: ["Sales Specialist", "Ops Concierge"],
        queue: ["Review CRM brief", "Classify feedback"],
        recent: ["Brief ready"],
        status: "ok",
        errors: ["Sync timeout"],
        completed: ["Lead intake"],
      },
      timeline: [],
      health: [],
      recommendations: [],
      mcOk: true,
      activeModules: ["ai", "crm"],
    };
    const rt = deriveRuntime(snapshot, [
      { id: "n1", kind: "workflow" as const, title: "Approve invoice", body: "x", createdAt: "", read: false },
    ]);
    expect(ORCH_CHAIN.map((s) => s.id)).toEqual([
      "user",
      "concierge",
      "ai_team",
      "workflow",
      "integrations",
      "knowledge",
      "completed",
    ]);
    expect(rt.counts.active).toBe(2);
    expect(rt.counts.waiting).toBe(2);
    expect(rt.counts.completed).toBe(1);
    expect(rt.counts.failed).toBe(1);
    expect(rt.counts.paused).toBeGreaterThanOrEqual(1);
    expect(rt.queue.length).toBeGreaterThan(0);
    expect(rt.orchestration.some((s) => s.active)).toBe(true);
    expect(rt.health.queueSize).toBeGreaterThan(0);
    expect(rt.health.needsIntervention).toBe(true);
    expect(rt.twin.aiInvolved.length).toBeGreaterThan(0);
  });
});

describe("Sprint 33.3 Enterprise Data Fabric", () => {
  it("builds graph, lineage, impact, knowledge chain", async () => {
    const { FABRIC_ENTITIES, KNOWLEDGE_CHAIN } = await import("../enterprise-data-fabric/fabricCatalog");
    const { deriveDataFabric } = await import("../enterprise-data-fabric/deriveFabric");
    expect(FABRIC_ENTITIES.map((e) => e.id)).toEqual(
      expect.arrayContaining([
        "company",
        "users",
        "ai_team",
        "clients",
        "deals",
        "documents",
        "workflows",
        "knowledge",
        "integrations",
      ]),
    );
    expect(KNOWLEDGE_CHAIN.map((s) => s.id)).toEqual([
      "knowledge",
      "documents",
      "clients",
      "workflows",
      "ai_team",
      "twin",
    ]);
    const fabric = deriveDataFabric(
      {
        updatedAt: new Date().toISOString(),
        activity: [
          {
            id: "a1",
            kind: "crm",
            title: "Deal updated",
            detail: "x",
            at: new Date().toISOString(),
            source: "seed",
          },
        ],
        aiOps: {
          running: ["Sales Specialist"],
          queue: ["Brief"],
          recent: ["Done"],
          status: "ok",
          errors: [],
          completed: ["Lead"],
        },
        timeline: [],
        health: [{ id: "knowledge" as const, label: "KB", ok: true, detail: "ok" }],
        recommendations: [],
        mcOk: true,
        activeModules: ["crm", "knowledge"],
      },
      { company: "Demo", roleId: "owner" },
    );
    expect(fabric.entities.length).toBe(FABRIC_ENTITIES.length);
    expect(fabric.edges.length).toBeGreaterThan(5);
    expect(fabric.lineage.knowledge?.source).toBeTruthy();
    expect(fabric.impact.deals?.dependsOn.length).toBeGreaterThan(0);
    expect(fabric.executive.linkedObjects).toBeGreaterThan(0);
    const exp = fabric.explore("knowledge");
    expect(exp.related.length).toBeGreaterThan(0);
    expect(exp.aiUsing.length).toBeGreaterThan(0);
  });
});

describe("Sprint 33.4 Predictive Intelligence", () => {
  it("forecasts metrics, scenarios, risks, twin zones", async () => {
    const { derivePredictive, WHAT_IF_SCENARIOS } = await import("../predictive-intelligence/derivePredictive");
    expect(WHAT_IF_SCENARIOS.map((s) => s.id)).toEqual(
      expect.arrayContaining(["grow_sales", "change_workflow", "disable_integration"]),
    );
    const pred = derivePredictive({
      updatedAt: new Date().toISOString(),
      activity: [
        { id: "1", kind: "crm", title: "Deal", detail: "", at: new Date().toISOString(), source: "seed" },
        { id: "2", kind: "deal", title: "Won", detail: "", at: new Date().toISOString(), source: "seed" },
      ],
      aiOps: {
        running: ["Sales Specialist", "Ops Concierge"],
        queue: ["A", "B"],
        recent: ["x"],
        status: "ok",
        errors: ["timeout"],
        completed: ["Lead"],
      },
      timeline: [],
      health: [{ id: "crm" as const, label: "CRM", ok: true, detail: "ok" }],
      recommendations: [],
      mcOk: true,
      activeModules: ["crm", "ai"],
    });
    expect(pred.forecasts.length).toBe(5);
    expect(pred.forecasts.some((f) => f.id === "kpi")).toBe(true);
    expect(pred.scenarios.length).toBe(3);
    expect(pred.risks.length).toBeGreaterThan(0);
    expect(pred.opportunities.length).toBeGreaterThan(0);
    expect(pred.executive.likelyToday.length).toBeGreaterThan(0);
    expect(pred.twinZones.length).toBe(4);
  });
});

describe("Sprint 33.5 Autonomous Enterprise", () => {
  it("supports levels, approvals, journal, governance", async () => {
    const { AUTONOMY_LEVELS, CRITICAL_ACTIONS, resolveDefaultLevel } = await import(
      "../autonomous-enterprise/autonomyCatalog"
    );
    const { setAutonomyLevel, decideApproval, listApprovals } = await import(
      "../autonomous-enterprise/autonomyState"
    );
    const { deriveAutonomy } = await import("../autonomous-enterprise/deriveAutonomy");

    expect(AUTONOMY_LEVELS).toHaveLength(5);
    expect(resolveDefaultLevel("platform_owner")).toBe(3);
    expect(CRITICAL_ACTIONS.length).toBeGreaterThan(3);

    setAutonomyLevel(3);
    const bundle = deriveAutonomy(
      {
        updatedAt: new Date().toISOString(),
        activity: [],
        aiOps: {
          running: ["Concierge"],
          queue: ["Q"],
          recent: [],
          status: "ok",
          errors: [],
          completed: ["Done"],
        },
        timeline: [],
        health: [],
        recommendations: [],
        mcOk: true,
        activeModules: ["crm"],
      },
      { roleId: "owner" },
    );
    expect(bundle.dashboard.level).toBe(3);
    expect(bundle.approvals.length).toBeGreaterThanOrEqual(6);
    expect(bundle.categories.map((c) => c.id)).toEqual(
      expect.arrayContaining(["crm", "finance", "legal", "documents", "ai_team", "workflow"]),
    );
    const pending = listApprovals().find((a) => a.status === "pending");
    expect(pending).toBeTruthy();
    decideApproval(pending!.id, "approved", "tester");
    expect(listApprovals().find((a) => a.id === pending!.id)?.status).toBe("approved");
    expect(bundle.governance.timeSavedMin).toBeGreaterThanOrEqual(0);
  });
});

describe("Sprint 33.6 Enterprise Control Tower", () => {
  it("composes overview, cockpit, ecosystems, incidents, commands", async () => {
    const { deriveControlTower, CONTROL_TOWER_COMMANDS } = await import(
      "../enterprise-control-tower/deriveControlTower"
    );
    expect(CONTROL_TOWER_COMMANDS.map((c) => c.id)).toEqual(
      expect.arrayContaining(["cmd_ws", "cmd_twin", "cmd_runtime", "cmd_approval", "cmd_builder", "cmd_mkt"]),
    );
    const tower = deriveControlTower(
      {
        updatedAt: new Date().toISOString(),
        activity: [
          { id: "1", kind: "crm", title: "Deal", detail: "", at: new Date().toISOString(), source: "seed" },
        ],
        aiOps: {
          running: ["Sales Specialist"],
          queue: ["Q1"],
          recent: [],
          status: "ok",
          errors: [],
          completed: ["Lead"],
        },
        timeline: [],
        health: [
          { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
          { id: "mission_control" as const, label: "MC", ok: true, detail: "ok" },
        ],
        recommendations: [],
        mcOk: true,
        activeModules: ["crm", "beauty", "ai"],
      },
      { company: "Demo Corp", roleId: "owner" },
    );
    expect(tower.overview.length).toBeGreaterThanOrEqual(7);
    expect(tower.cockpit.some((k) => k.id === "revenue")).toBe(true);
    expect(tower.ecosystems.map((e) => e.id)).toEqual(
      expect.arrayContaining(["beauty", "legal", "cafe", "agro", "auto", "drone", "crypto"]),
    );
    expect(tower.operations.length).toBeGreaterThan(0);
    expect(tower.incidents.length).toBeGreaterThan(0);
    expect(tower.commands.length).toBe(6);
  });
});

describe("Sprint 33.7 Self-Learning Enterprise", () => {
  it("derives metrics, workflow opts, AI review, knowledge, recommendations, executive", async () => {
    const { deriveLearning } = await import("../self-learning-enterprise/deriveLearning");
    const bundle = deriveLearning({
      updatedAt: new Date().toISOString(),
      activity: [
        { id: "1", kind: "crm", title: "Follow-up", detail: "", at: new Date().toISOString(), source: "seed" },
        { id: "2", kind: "automation", title: "Invoice", detail: "", at: new Date().toISOString(), source: "seed" },
      ],
      aiOps: {
        running: ["Sales Specialist"],
        queue: ["Q1", "Q2"],
        recent: ["Ops Copilot"],
        status: "ok",
        errors: ["timeout"],
        completed: ["Lead score", "Doc draft"],
      },
      timeline: [],
      health: [
        { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
        { id: "mission_control" as const, label: "MC", ok: true, detail: "ok" },
      ],
      recommendations: [],
      mcOk: true,
      activeModules: ["crm", "ai", "knowledge"],
    });
    expect(bundle.metrics.map((m) => m.id)).toEqual(
      expect.arrayContaining(["ai_eff", "wf_eff", "speed", "reco_q", "auto_ok"]),
    );
    expect(bundle.workflowOpts.length).toBeGreaterThanOrEqual(4);
    expect(bundle.aiReview.length).toBeGreaterThan(0);
    expect(bundle.knowledge.topUsed.length).toBeGreaterThan(0);
    expect(bundle.recommendations.some((r) => r.category === "workflow")).toBe(true);
    expect(bundle.recommendations.some((r) => r.category === "knowledge")).toBe(true);
    expect(bundle.executive.learned.length).toBeGreaterThan(0);
    expect(bundle.timeSavedMin).toBeGreaterThanOrEqual(0);
  });
});

describe("Sprint 33.8 Enterprise Strategy & OKR Intelligence", () => {
  it("derives goals, OKR cards, alignments, executive, timeline, scenario impacts", async () => {
    const { deriveOkr, alignRecommendation, ENTERPRISE_GOALS } = await import("../enterprise-okr");
    expect(ENTERPRISE_GOALS.map((g) => g.domain)).toEqual(
      expect.arrayContaining([
        "revenue",
        "profit",
        "sales",
        "marketing",
        "production",
        "customer_success",
        "hr",
        "operations",
      ]),
    );
    const bundle = deriveOkr({
      updatedAt: new Date().toISOString(),
      activity: [
        { id: "1", kind: "crm", title: "Deal close", detail: "", at: new Date().toISOString(), source: "seed" },
      ],
      aiOps: {
        running: ["Sales Specialist"],
        queue: ["Q1"],
        recent: ["Concierge"],
        status: "ok",
        errors: [],
        completed: ["Lead"],
      },
      timeline: [],
      health: [
        { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
        { id: "mission_control" as const, label: "MC", ok: true, detail: "ok" },
      ],
      recommendations: [
        { id: "r1", title: "Accelerate CRM follow-up", tone: "improve" },
        { id: "r2", title: "Reduce Runtime queue", tone: "risk" },
      ],
      mcOk: true,
      activeModules: ["crm", "ai"],
    });
    expect(bundle.goals.length).toBe(8);
    expect(bundle.okrCards.length).toBe(8);
    expect(bundle.goals.every((g) => g.kpi && g.owner && g.deadline)).toBe(true);
    expect(bundle.alignments.length).toBeGreaterThan(0);
    expect(bundle.alignments[0]!.goalLabel).toBeTruthy();
    expect(bundle.alignments[0]!.kpi).toBeTruthy();
    expect(bundle.scenarioImpacts[0]!.ifDone).toBeTruthy();
    expect(bundle.scenarioImpacts[0]!.ifSkipped).toBeTruthy();
    expect(bundle.executive.today.length).toBeGreaterThan(0);
    expect(bundle.timeline.map((t) => t.status)).toEqual(
      expect.arrayContaining(["in_progress"]),
    );
    expect(bundle.mc.progressAvg).toBeGreaterThanOrEqual(0);
    const aligned = alignRecommendation(
      { id: "x", title: "Fix sales pipeline bottleneck" },
      bundle.goals,
    );
    expect(aligned.goalLabel).toBeTruthy();
    expect(aligned.expectedEffect).toContain("%");
  });
});

describe("Sprint 33.9 Enterprise Governance", () => {
  it("derives policies, validation pipeline, approvals, audit, risks, AI governance, compliance", async () => {
    const { deriveGovernance, ENTERPRISE_POLICIES } = await import("../enterprise-governance");
    expect(ENTERPRISE_POLICIES.map((p) => p.domain)).toEqual(
      expect.arrayContaining([
        "financial",
        "security",
        "legal",
        "privacy",
        "hr",
        "operations",
        "ai_usage",
        "automation",
      ]),
    );
    const bundle = deriveGovernance(
      {
        updatedAt: new Date().toISOString(),
        activity: [
          { id: "1", kind: "ai", title: "Concierge decision", detail: "ok", at: new Date().toISOString(), source: "seed" },
        ],
        aiOps: {
          running: ["Concierge"],
          queue: ["Q1"],
          recent: ["Ops Copilot"],
          status: "ok",
          errors: [],
          completed: ["Doc draft"],
        },
        timeline: [],
        health: [
          { id: "crm" as const, label: "CRM", ok: true, detail: "ok" },
          { id: "mission_control" as const, label: "MC", ok: true, detail: "ok" },
        ],
        recommendations: [],
        mcOk: true,
        activeModules: ["crm", "ai"],
      },
      { roleId: "owner", permissions: ["read", "write", "admin"] },
    );
    expect(bundle.policies.length).toBe(8);
    expect(bundle.validations.length).toBeGreaterThan(0);
    expect(bundle.validations[0]!.steps.map((s) => s.id)).toEqual([
      "policy",
      "permission",
      "approval",
      "execution",
    ]);
    expect(bundle.approvalQueue.length).toBeGreaterThan(0);
    expect(bundle.auditTimeline.length).toBeGreaterThan(0);
    expect(bundle.risks.map((r) => r.kind)).toEqual(
      expect.arrayContaining(["security", "compliance", "operational", "ai", "integration"]),
    );
    expect(bundle.aiGovernance.length).toBeGreaterThan(0);
    expect(bundle.compliance.compliancePct).toBeGreaterThanOrEqual(0);
    expect(bundle.compliance.auditScore).toBeGreaterThanOrEqual(0);
  });
});

describe("Sprint 30.1 Enterprise Authentication", () => {
  it("exposes enterprise roles and access middleware", async () => {
    const { roleManager, roleResolver, accessMiddleware } = await import("../../auth/managers");
    const names = roleManager.enterpriseRoles().map((r) => r.name);
    for (const n of [
      "Owner",
      "Administrator",
      "Manager",
      "Employee",
      "Client",
      "Dealer",
      "Partner",
      "Accountant",
      "Lawyer",
      "Production",
      "Viewer",
    ]) {
      expect(names).toContain(n);
    }
    expect(roleResolver.permissionGroups(["Owner"]).length).toBeGreaterThan(0);
    expect(
      accessMiddleware({ roles: ["owner"], permissions: [] }, "administration"),
    ).toBe(true);
    expect(
      accessMiddleware({ roles: ["viewer"], permissions: ["analytics.read"] }, "analytics.read"),
    ).toBe(true);
  });

  it("exports Russian auth i18n keys", async () => {
    const { messages } = await import("../i18n/messages");
    expect(messages.ru["auth.google"]).toMatch(/Google/);
    expect(messages.ru["auth.emailLogin"]).toMatch(/Email/);
    expect(messages.ru["auth.createAccount"]).toBeTruthy();
    expect(messages.ru["auth.resetPassword"]).toBeTruthy();
  });
});

describe("Sprint 30.2 Enterprise Navigation & Russian UI", () => {
  it("defines Russian sidebar and owner nav", async () => {
    const { ENTERPRISE_RU_SIDEBAR, OWNER_RU_NAV, ROLE_SWITCHER_OPTIONS, RU_QUICK_ACTIONS } =
      await import("../navigation/enterpriseRuNav");
    const labels = ENTERPRISE_RU_SIDEBAR.map((i) => i.label);
    for (const required of [
      "Главная",
      "Рабочий стол",
      "Город",
      "AI-Агенты",
      "CRM",
      "ERP",
      "Проекты",
      "Клиенты",
      "Финансы",
      "Документы",
      "Продакшн",
      "AI Studio",
      "Производство",
      "Юридический отдел",
      "Аналитика",
      "Мониторинг",
      "Настройки",
      "Знания",
      "Задачи",
      "Календарь",
      "Уведомления",
      "Маркетплейс",
      "Пользователи",
    ]) {
      expect(labels).toContain(required);
    }
    expect(OWNER_RU_NAV.some((i) => i.route === "/owner")).toBe(true);
    expect(OWNER_RU_NAV.some((i) => i.route === "/admin")).toBe(true);
    expect(OWNER_RU_NAV.some((i) => i.route === "/health")).toBe(true);
    expect(ROLE_SWITCHER_OPTIONS.map((r) => r.id)).toEqual(
      expect.arrayContaining([
        "owner",
        "administrator",
        "manager",
        "employee",
        "dealer",
        "partner",
        "client",
        "viewer",
      ]),
    );
    expect(RU_QUICK_ACTIONS.map((a) => a.label)).toEqual(
      expect.arrayContaining([
        "Открыть модуль",
        "Открыть клиента",
        "Открыть проект",
        "Открыть AI-агента",
        "Создать клиента",
        "Создать проект",
        "Создать документ",
        "Открыть карту",
        "Создать задачу",
      ]),
    );
  });

  it("defaults locale to Russian and exposes nav i18n", async () => {
    const { webConfig } = await import("../config/webConfig");
    expect(webConfig.defaultLocale).toBe("ru");
    const { messages } = await import("../i18n/messages");
    expect(messages.ru["nav.mainMenu"]).toBe("Основное меню");
    expect(messages.ru["nav.ownerMode"]).toBe("Режим владельца");
    expect(messages.ru["role.switcher"]).toBe("Роль");
    expect(messages.ru["org.switcher"]).toBe("Компания");
    expect(messages.ru["common.searchPlaceholder"]).toMatch(/поиск/i);
  });

  it("indexes Russian search hits for clients and quick actions", async () => {
    const { searchIndex } = await import("../../navigation/managers/searchIndex");
    const { searchProvider } = await import("../../navigation/managers/searchProvider");
    expect(searchIndex.list().some((d) => d.title.includes("Клиент") || d.path.includes("/crm"))).toBe(
      true,
    );
    const hits = searchProvider.search("клиент");
    expect(hits.length).toBeGreaterThan(0);
    const mapHits = searchProvider.search("карта");
    expect(mapHits.some((h) => h.path.includes("city") || h.path.includes("enterprise-city"))).toBe(true);
  });

  it("exports owner dashboard page", async () => {
    const mod = await import("../navigation/OwnerDashboardPage");
    expect(typeof mod.OwnerDashboardPage).toBe("function");
  });
});

describe("Sprint 30.3 Beta Launch", () => {
  it("exposes beta home catalog sections", async () => {
    const cat = await import("../dashboard/betaHomeCatalog");
    expect(cat.BETA_RECENT_PROJECTS.length).toBeGreaterThan(0);
    expect(cat.CLIENT_DASHBOARD_SECTIONS.map((s) => s.title)).toEqual(
      expect.arrayContaining(["Мои заявки", "Мои проекты", "Мои документы", "Мои сообщения", "История"]),
    );
    expect(cat.DEALER_DASHBOARD_SECTIONS.map((s) => s.title)).toEqual(
      expect.arrayContaining(["Клиенты", "Заказы", "Статистика", "Продажи", "CRM"]),
    );
    expect(cat.OWNER_BETA_METRICS.length).toBeGreaterThanOrEqual(8);
    expect(cat.COMING_SOON_RU).toBe("Скоро будет доступно");
    expect(cat.BETA_PRODUCTION_STUDIOS.every((s) => s.available)).toBe(true);
    expect(cat.BETA_PRODUCTION_STUDIOS.some((s) => s.id === "presentation")).toBe(true);
  });

  it("routes roles to beta homes", async () => {
    const { homeRouteForRole, postAuthDestination } = await import("../navigation/roleHome");
    expect(homeRouteForRole("owner")).toBe("/owner");
    expect(homeRouteForRole("administrator")).toBe("/admin");
    expect(homeRouteForRole("manager")).toBe("/dashboards/manager");
    expect(homeRouteForRole("employee")).toBe("/dashboards/employee");
    expect(homeRouteForRole("client")).toBe("/dashboards/client");
    expect(homeRouteForRole("dealer")).toBe("/dashboards/dealer");
    const { resetFirstEntry } = await import("../onboarding/firstEntryStore");
    resetFirstEntry();
    expect(postAuthDestination("owner")).toBe("/onboarding/first-entry");
  });

  it("exports dashboard and invitation pages", async () => {
    expect(typeof (await import("../dashboard/BetaHomeDashboard")).BetaHomeDashboard).toBe(
      "function",
    );
    expect(typeof (await import("../dashboard/ClientDashboardPage")).ClientDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("../dashboard/DealerDashboardPage")).DealerDashboardPage).toBe(
      "function",
    );
    expect(typeof (await import("../pages/InvitationPage")).InvitationPage).toBe("function");
    expect(typeof (await import("../enterprise-city/CityPreviewPanel")).CityPreviewPanel).toBe(
      "function",
    );
  });

  it("keeps Google login and register API exports", async () => {
    const api = await import("../auth/identityApi");
    expect(typeof api.productionGoogleLogin).toBe("function");
    expect(typeof api.productionRegister).toBe("function");
    expect(typeof api.productionPasswordReset).toBe("function");
    const store = await import("../auth/authStore");
    expect(typeof store.useAuthStore.getState().loginWithGoogle).toBe("function");
    expect(typeof store.useAuthStore.getState().register).toBe("function");
  });
});
