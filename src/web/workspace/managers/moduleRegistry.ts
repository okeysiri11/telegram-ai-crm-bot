/**
 * Centralized Module Registry — Sprint 30.5.
 * Extends Sprint 30.4 shells. Every business ecosystem registers here.
 * Single source of truth for routes / permissions / health — no parallel catalogs.
 */

export type ModuleHealth = "healthy" | "degraded" | "unknown" | "offline";

export type ModuleMeta = {
  title: string;
  purpose: string;
  builderRoute?: string;
  portalHint?: string;
  apiHint?: string;
  ecosystem?: string;
  permissions?: string[];
};

/** Full registry entry required by Sprint 30.5. */
export type RegisteredModule = ModuleMeta & {
  id: string;
  name: string;
  version: string;
  routes: string[];
  permissions: string[];
  navigation: { id: string; label: string; route: string }[];
  widgets: string[];
  dashboards: string[];
  dependencies: string[];
  health: ModuleHealth;
  kind: "universal" | "ecosystem" | "platform";
};

function entry(
  id: string,
  meta: ModuleMeta & {
    version?: string;
    widgets?: string[];
    dashboards?: string[];
    dependencies?: string[];
    health?: ModuleHealth;
    kind?: RegisteredModule["kind"];
    extraRoutes?: string[];
  },
): RegisteredModule {
  const route = `/workspace/${id}`;
  const permissions = meta.permissions?.length ? meta.permissions : ["read"];
  const nav: RegisteredModule["navigation"] = [
    { id: `nav_${id}`, label: meta.title, route },
  ];
  if (meta.builderRoute) {
    nav.push({ id: `nav_${id}_builder`, label: `${meta.title} Builder`, route: meta.builderRoute });
  }
  if (meta.portalHint) {
    nav.push({ id: `nav_${id}_portal`, label: `${meta.title} Portal`, route: meta.portalHint });
  }
  return {
    id,
    name: meta.title,
    title: meta.title,
    purpose: meta.purpose,
    version: meta.version || "1.0.0-shell",
    routes: [route, ...(meta.extraRoutes || [])],
    permissions,
    navigation: nav,
    widgets: meta.widgets || [`widget_${id}_status`],
    dashboards: meta.dashboards || [`dash_${id}_overview`],
    dependencies: meta.dependencies || ["enterprise_web_platform", "platform_builder"],
    health: meta.health || "healthy",
    kind: meta.kind || (meta.ecosystem ? "ecosystem" : "universal"),
    builderRoute: meta.builderRoute,
    portalHint: meta.portalHint,
    apiHint: meta.apiHint,
    ecosystem: meta.ecosystem,
  };
}

const MODULES: Record<string, RegisteredModule> = {
  crm: entry("crm", {
    title: "CRM",
    purpose: "Universal CRM module shell — extends Platform Builder CRM frame and vertical CRM APIs.",
    builderRoute: "/platform-builder/crm",
    portalHint: "/portals/employee",
    apiHint: "Vertical CRM APIs (e.g. dealer CRM) + legacy /api/v1",
    permissions: ["crm", "read"],
    version: "1.0.0-shell",
    widgets: ["widget_crm_pipeline", "widget_crm_leads"],
    dashboards: ["dash_crm_overview"],
  }),
  erp: entry("erp", {
    title: "ERP",
    purpose: "Universal ERP module shell — compose inventory/ops without duplicating automotive ERP.",
    builderRoute: "/platform-builder/erp",
    portalHint: "/portals/employee",
    permissions: ["erp", "read"],
  }),
  finance: entry("finance", {
    title: "Finance",
    purpose: "Finance module shell — binds to finance_enterprise APIs in later sprints.",
    apiHint: "/api/finance-enterprise/v1",
    permissions: ["finance", "read"],
    version: "5.2.0-enterprise",
    dependencies: ["enterprise_web_platform", "finance_enterprise"],
  }),
  analytics: entry("analytics", {
    title: "Analytics",
    purpose: "Analytics module shell — reuses Visual Intelligence and hub analytics.",
    builderRoute: "/platform-builder/intelligence",
    portalHint: "/portals/owner",
    permissions: ["read"],
  }),
  marketplace: entry("marketplace", {
    title: "Marketplace",
    purpose: "Marketplace module shell — Platform Builder marketplace frame + marketplace app API.",
    builderRoute: "/platform-builder/marketplace",
    apiHint: "/api/marketplace/v1",
    permissions: ["read"],
  }),
  ai: entry("ai", {
    title: "AI Workspace",
    purpose: "AI module shell — Concierge, Team, and AI OS remain platform layers.",
    builderRoute: "/platform-builder/ai-team",
    portalHint: "/ai-os",
    permissions: ["read"],
    kind: "platform",
    dependencies: ["enterprise_web_platform", "platform_builder", "ai_os"],
  }),
  auto: entry("auto", {
    title: "Automotive",
    purpose: "Automotive industry module shell — prepares Customer/Dealer portals for auto APIs.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/auto/v1",
    ecosystem: "automotive",
    version: "4.2.0-enterprise",
    dependencies: ["enterprise_web_platform", "auto_marketplace", "platform_builder"],
    widgets: ["widget_auto_inventory", "widget_auto_leads"],
    dashboards: ["dash_auto_dealer"],
  }),
  beauty: entry("beauty", {
    title: "Beauty",
    purpose: "Beauty industry module — Salon CRM, appointments, calendar via BOS/BWS/BCJ; shared Concierge/MC/OBS.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/enterprise-bos/v1 · /api/enterprise-bws/v1 · /api/enterprise-bcj/v1",
    ecosystem: "beauty",
    version: "1.1.0-pilot",
    dependencies: ["enterprise_web_platform", "platform_beauty", "platform_builder", "enterprise_hub"],
    widgets: ["widget_beauty_schedule", "widget_beauty_appointments"],
    dashboards: ["dash_beauty_owner"],
  }),
  cafe: entry("cafe", {
    title: "Cafe",
    purpose: "Cafe F&B pilot — tables, menu, reservations, kitchen via Cafe OS; payments/loyalty via ECO.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/enterprise-cos/v1 · /api/enterprise-eco/v1",
    ecosystem: "cafe",
    version: "1.0.0-pilot",
    dependencies: ["enterprise_web_platform", "platform_cafe_os", "platform_builder", "enterprise_hub"],
    widgets: ["widget_cafe_kitchen", "widget_cafe_reservations"],
    dashboards: ["dash_cafe_owner"],
  }),
  agro: entry("agro", {
    title: "Agriculture",
    purpose:
      "Agriculture operational pilot — farm CRM, harvest, warehouse, grain marketplace, export contracts, sea freight via agro + supply-chain APIs; shared Concierge/MC/OBS.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint:
      "/api/agro/v1 · /api/agro-supply-chain/v1 · /api/agro-enterprise/v1 · /api/ai-agronomist/v1",
    ecosystem: "agriculture",
    version: "1.0.0-pilot",
    dependencies: [
      "enterprise_web_platform",
      "agro_marketplace",
      "agro_enterprise",
      "platform_builder",
      "enterprise_hub",
    ],
    widgets: ["widget_agro_harvest", "widget_agro_shipments"],
    dashboards: ["dash_agro_owner", "dash_agro_export"],
  }),
  drone: entry("drone", {
    title: "Drone",
    purpose:
      "Drone operational pilot — projects, fleet, production, warehouse, testing, missions, telemetry via /api/drone/v1; shared Concierge/MC/OBS.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/drone/v1 · /api/precision-agriculture/v1",
    ecosystem: "drone",
    version: "1.0.0-pilot",
    dependencies: [
      "enterprise_web_platform",
      "drone_platform",
      "agro_enterprise",
      "platform_builder",
      "enterprise_hub",
    ],
    widgets: ["widget_drone_fleet", "widget_drone_missions"],
    dashboards: ["dash_drone_owner", "dash_drone_executive"],
  }),
  legal: entry("legal", {
    title: "Legal",
    purpose:
      "Legal operational pilot — law-firm CRM, cases, hearings, document automation via legal-cm/di/cp/aa; shared Concierge/MC/OBS.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint:
      "/api/legal-enterprise/v1 · /api/legal-cm/v1 · /api/legal-di/v1 · /api/legal-aa/v1 · /api/legal-ei/v1",
    ecosystem: "legal",
    version: "1.0.0-pilot",
    dependencies: [
      "enterprise_web_platform",
      "legal_enterprise",
      "platform_builder",
      "enterprise_hub",
    ],
    widgets: ["widget_legal_cases", "widget_legal_calendar"],
    dashboards: ["dash_legal_owner", "dash_legal_executive"],
  }),
  crypto: entry("crypto", {
    title: "Crypto (Bidex)",
    purpose:
      "Bidex operational pilot — KYC/AML, wallets, OTC, approvals, settlement via finance-da/pay/tr/int + legal-cp; shared Concierge/MC/OBS.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint:
      "/api/finance-da/v1 · /api/finance-pay/v1 · /api/finance-tr/v1 · /api/finance-int/v1 · /api/legal-cp/v1 · /api/crypto-enterprise/v1",
    ecosystem: "crypto",
    version: "1.0.0-pilot",
    dependencies: [
      "enterprise_web_platform",
      "finance_enterprise",
      "crypto_enterprise",
      "legal_enterprise",
      "platform_builder",
      "enterprise_hub",
    ],
    widgets: ["widget_bidex_wallets", "widget_bidex_otc"],
    dashboards: ["dash_bidex_owner", "dash_bidex_treasury"],
  }),
  hr: entry("hr", {
    title: "HR",
    purpose: "HR directory shell — placeholder until HR universal module binds live data.",
    permissions: ["read"],
  }),
  docs: entry("docs", {
    title: "Documents / Knowledge",
    purpose: "Documents shell — Knowledge Builder frame + knowledge graph extensions.",
    builderRoute: "/platform-builder/knowledge",
    permissions: ["read"],
  }),
  reports: entry("reports", {
    title: "Reports",
    purpose: "Reports shell — compose analytics and executive timeline views.",
    portalHint: "/portals/owner",
    permissions: ["read"],
  }),
  workflows: entry("workflows", {
    title: "Workflows",
    purpose: "Workflows shell — Workflow Studio + Workflow Intelligence (analysis-only in PB).",
    builderRoute: "/platform-builder/workflow-intelligence",
    permissions: ["read"],
  }),
};

/** Platform-level modules registered alongside workspace shells (no duplicate routes). */
const PLATFORM_MODULES: RegisteredModule[] = [
  {
    id: "mission_control",
    name: "Mission Control",
    title: "Mission Control",
    purpose: "Unified executive operating center — aggregates existing services.",
    version: "1.36.0",
    routes: ["/platform-builder/mission-control", "/portals/mission-control"],
    permissions: ["read"],
    navigation: [
      { id: "nav_mc", label: "Mission Control", route: "/platform-builder/mission-control" },
    ],
    widgets: ["widget_mc_overview", "widget_mc_health"],
    dashboards: ["dash_mission_control", "dash_pilot"],
    dependencies: ["platform_builder", "enterprise_obs"],
    health: "healthy",
    kind: "platform",
    builderRoute: "/platform-builder/mission-control",
  },
  {
    id: "pilot",
    name: "Pilot Dashboard",
    title: "Pilot Dashboard",
    purpose: "First internal pilot readiness surface — status, modules, telemetry.",
    version: "1.36.0",
    routes: ["/pilot"],
    permissions: ["read", "admin"],
    navigation: [{ id: "nav_pilot", label: "Pilot Dashboard", route: "/pilot" }],
    widgets: ["widget_pilot_status", "widget_pilot_errors"],
    dashboards: ["dash_pilot"],
    dependencies: ["enterprise_web_platform", "enterprise_obs", "module_registry"],
    health: "healthy",
    kind: "platform",
  },
];

export const BUSINESS_ECOSYSTEM_KEYS = [
  "auto",
  "beauty",
  "cafe",
  "agro",
  "drone",
  "legal",
  "crypto",
] as const;

export type BusinessEcosystemKey = (typeof BUSINESS_ECOSYSTEM_KEYS)[number];

/** Backward-compatible alias used by WorkspaceModulePage shells. */
export const WORKSPACE_MODULES: Record<string, ModuleMeta> = Object.fromEntries(
  Object.entries(MODULES).map(([k, v]) => [
    k,
    {
      title: v.title,
      purpose: v.purpose,
      builderRoute: v.builderRoute,
      portalHint: v.portalHint,
      apiHint: v.apiHint,
      ecosystem: v.ecosystem,
      permissions: v.permissions,
    },
  ]),
);

function allModules(): RegisteredModule[] {
  return [...Object.values(MODULES), ...PLATFORM_MODULES];
}

export const moduleRegistry = {
  get(id: string): RegisteredModule | undefined {
    return MODULES[id] || PLATFORM_MODULES.find((m) => m.id === id);
  },
  resolve(id: string): ModuleMeta {
    const m = this.get(id);
    if (m) {
      return {
        title: m.title,
        purpose: m.purpose,
        builderRoute: m.builderRoute,
        portalHint: m.portalHint,
        apiHint: m.apiHint,
        ecosystem: m.ecosystem,
        permissions: m.permissions,
      };
    }
    return {
      title: id,
      purpose: "Workspace module shell — Sprint 30.5 web core.",
      permissions: ["read"],
    };
  },
  list(): string[] {
    return Object.keys(MODULES);
  },
  listRegistered(): RegisteredModule[] {
    return allModules();
  },
  ecosystems(): BusinessEcosystemKey[] {
    return [...BUSINESS_ECOSYSTEM_KEYS];
  },
  ecosystemModules(): RegisteredModule[] {
    return BUSINESS_ECOSYSTEM_KEYS.map((k) => MODULES[k]).filter(Boolean);
  },
  routeFor(id: string): string {
    return `/workspace/${id}`;
  },
  /** Register or replace a module (tests / dynamic extension — no parallel registry). */
  register(module: RegisteredModule): RegisteredModule {
    if (module.kind === "platform" || module.id === "mission_control" || module.id === "pilot") {
      const idx = PLATFORM_MODULES.findIndex((m) => m.id === module.id);
      if (idx >= 0) PLATFORM_MODULES[idx] = module;
      else PLATFORM_MODULES.push(module);
      return module;
    }
    MODULES[module.id] = module;
    WORKSPACE_MODULES[module.id] = {
      title: module.title,
      purpose: module.purpose,
      builderRoute: module.builderRoute,
      portalHint: module.portalHint,
      apiHint: module.apiHint,
      ecosystem: module.ecosystem,
      permissions: module.permissions,
    };
    return module;
  },
  healthSummary(): { id: string; name: string; health: ModuleHealth; version: string; kind: string }[] {
    return allModules().map((m) => ({
      id: m.id,
      name: m.name,
      health: m.health,
      version: m.version,
      kind: m.kind,
    }));
  },
  /** Validate every ecosystem is registered (pilot gate). */
  ecosystemsRegistered(): boolean {
    return BUSINESS_ECOSYSTEM_KEYS.every((k) => Boolean(MODULES[k]));
  },
};
