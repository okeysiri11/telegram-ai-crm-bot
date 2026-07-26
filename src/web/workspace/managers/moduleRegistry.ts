/**
 * Shared workspace module registry — Sprint 30.4.
 * Single source for soft-route shells; modules load through FullLayout / WorkspaceLayout.
 * Does not reimplement vertical backends.
 */

export type ModuleMeta = {
  title: string;
  purpose: string;
  builderRoute?: string;
  portalHint?: string;
  apiHint?: string;
  /** Industry / business ecosystem key when applicable */
  ecosystem?: string;
  permissions?: string[];
};

export const WORKSPACE_MODULES: Record<string, ModuleMeta> = {
  crm: {
    title: "CRM",
    purpose: "Universal CRM module shell — extends Platform Builder CRM frame and vertical CRM APIs.",
    builderRoute: "/platform-builder/crm",
    portalHint: "/portals/employee",
    apiHint: "Vertical CRM APIs (e.g. dealer CRM) + legacy /api/v1",
    permissions: ["crm", "read"],
  },
  erp: {
    title: "ERP",
    purpose: "Universal ERP module shell — compose inventory/ops without duplicating automotive ERP.",
    builderRoute: "/platform-builder/erp",
    portalHint: "/portals/employee",
    permissions: ["erp", "read"],
  },
  finance: {
    title: "Finance",
    purpose: "Finance module shell — binds to finance_enterprise APIs in later sprints.",
    apiHint: "/api/finance-enterprise/v1",
    permissions: ["finance", "read"],
  },
  analytics: {
    title: "Analytics",
    purpose: "Analytics module shell — reuses Visual Intelligence and hub analytics.",
    builderRoute: "/platform-builder/intelligence",
    portalHint: "/portals/owner",
    permissions: ["read"],
  },
  marketplace: {
    title: "Marketplace",
    purpose: "Marketplace module shell — Platform Builder marketplace frame + marketplace app API.",
    builderRoute: "/platform-builder/marketplace",
    apiHint: "/api/marketplace/v1",
    permissions: ["read"],
  },
  ai: {
    title: "AI Workspace",
    purpose: "AI module shell — Concierge, Team, and AI OS remain platform layers.",
    builderRoute: "/platform-builder/ai-team",
    portalHint: "/ai-os",
    permissions: ["read"],
  },
  auto: {
    title: "Automotive",
    purpose: "Automotive industry module shell — prepares Customer/Dealer portals for auto APIs.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/auto/v1",
    ecosystem: "automotive",
    permissions: ["read"],
  },
  beauty: {
    title: "Beauty",
    purpose: "Beauty industry module shell — extends platform_beauty libraries + hub BOS.",
    builderRoute: "/platform-builder/business-ecosystem",
    ecosystem: "beauty",
    permissions: ["read"],
  },
  cafe: {
    title: "Cafe",
    purpose: "Cafe industry module shell — connection point only; no parallel cafe stack.",
    builderRoute: "/platform-builder/business-ecosystem",
    ecosystem: "cafe",
    permissions: ["read"],
  },
  agro: {
    title: "Agriculture",
    purpose: "Agriculture industry module shell — grain/trade/port capabilities via agro APIs.",
    builderRoute: "/platform-builder/business-ecosystem",
    apiHint: "/api/agro/v1 · /api/agro-enterprise/v1",
    ecosystem: "agriculture",
    permissions: ["read"],
  },
  drone: {
    title: "Drone",
    purpose: "Drone industry module shell — connection point via shared Business Ecosystem Foundation.",
    builderRoute: "/platform-builder/business-ecosystem",
    ecosystem: "drone",
    permissions: ["read"],
  },
  legal: {
    title: "Legal",
    purpose: "Legal industry module shell — binds to legal_enterprise without forking identity.",
    builderRoute: "/platform-builder/business-ecosystem",
    apiHint: "/api/legal-enterprise/v1",
    ecosystem: "legal",
    permissions: ["read"],
  },
  crypto: {
    title: "Crypto (Bidex)",
    purpose: "Crypto / Bidex module shell — reuses crypto_enterprise route ownership.",
    builderRoute: "/platform-builder/business-ecosystem",
    apiHint: "/api/crypto-enterprise/v1",
    ecosystem: "crypto",
    permissions: ["read"],
  },
  hr: {
    title: "HR",
    purpose: "HR directory shell — placeholder until HR universal module binds live data.",
    permissions: ["read"],
  },
  docs: {
    title: "Documents / Knowledge",
    purpose: "Documents shell — Knowledge Builder frame + knowledge graph extensions.",
    builderRoute: "/platform-builder/knowledge",
    permissions: ["read"],
  },
  reports: {
    title: "Reports",
    purpose: "Reports shell — compose analytics and executive timeline views.",
    portalHint: "/portals/owner",
    permissions: ["read"],
  },
  workflows: {
    title: "Workflows",
    purpose: "Workflows shell — Workflow Studio + Workflow Intelligence (analysis-only in PB).",
    builderRoute: "/platform-builder/workflow-intelligence",
    permissions: ["read"],
  },
};

/** Business ecosystems expected by Sprint 30.4 connection points. */
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

export const moduleRegistry = {
  get(id: string): ModuleMeta | undefined {
    return WORKSPACE_MODULES[id];
  },
  resolve(id: string): ModuleMeta {
    return (
      WORKSPACE_MODULES[id] || {
        title: id,
        purpose: "Workspace module shell — Sprint 30.4 web foundation.",
        permissions: ["read"],
      }
    );
  },
  list(): string[] {
    return Object.keys(WORKSPACE_MODULES);
  },
  ecosystems(): BusinessEcosystemKey[] {
    return [...BUSINESS_ECOSYSTEM_KEYS];
  },
  routeFor(id: string): string {
    return `/workspace/${id}`;
  },
};
