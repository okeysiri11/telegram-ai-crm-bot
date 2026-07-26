/**
 * Enterprise City building catalog — Sprint 32.3.3.
 * Visual navigation only: each building opens an existing route.
 * No new Navigation Engine / business logic.
 */

export type CityBuildingId =
  | "crm"
  | "analytics"
  | "ai_team"
  | "knowledge"
  | "documents"
  | "finance"
  | "production"
  | "marketing"
  | "sales"
  | "hr"
  | "admin"
  | "hub"
  | "mission_control"
  | "dashboard"
  | "concierge";

export type CityActivityTone = "idle" | "active" | "busy" | "alert";

export type CityBuilding = {
  id: CityBuildingId;
  label: string;
  short: string;
  icon: string;
  route: string;
  /** Map coordinates in 0–100 space (percent of city plane). */
  x: number;
  y: number;
  w: number;
  h: number;
  district: "commerce" | "ops" | "people" | "intel" | "hub";
  searchTokens: string[];
};

/** Buildings → existing Workspace / Platform Builder pages. */
export const CITY_BUILDINGS: CityBuilding[] = [
  {
    id: "hub",
    label: "Enterprise Hub",
    short: "Hub",
    icon: "🌍",
    route: "/workspace",
    x: 42,
    y: 38,
    w: 16,
    h: 18,
    district: "hub",
    searchTokens: ["hub", "enterprise", "workspace", "home"],
  },
  {
    id: "crm",
    label: "CRM Center",
    short: "CRM",
    icon: "🏢",
    route: "/workspace/crm",
    x: 12,
    y: 22,
    w: 14,
    h: 14,
    district: "commerce",
    searchTokens: ["crm", "clients", "pipeline"],
  },
  {
    id: "sales",
    label: "Sales",
    short: "Sales",
    icon: "🛒",
    route: "/workspace/crm",
    x: 28,
    y: 18,
    w: 12,
    h: 12,
    district: "commerce",
    searchTokens: ["sales", "deals", "funnel"],
  },
  {
    id: "marketing",
    label: "Marketing",
    short: "Mkt",
    icon: "📣",
    route: "/workspace",
    x: 14,
    y: 48,
    w: 12,
    h: 12,
    district: "commerce",
    searchTokens: ["marketing", "campaigns", "growth"],
  },
  {
    id: "finance",
    label: "Finance",
    short: "Fin",
    icon: "💰",
    route: "/workspace/finance",
    x: 28,
    y: 52,
    w: 12,
    h: 13,
    district: "commerce",
    searchTokens: ["finance", "billing", "treasury"],
  },
  {
    id: "analytics",
    label: "Analytics Center",
    short: "BI",
    icon: "📈",
    route: "/platform-builder/intelligence",
    x: 62,
    y: 16,
    w: 14,
    h: 14,
    district: "intel",
    searchTokens: ["analytics", "intelligence", "kpi", "reports"],
  },
  {
    id: "ai_team",
    label: "AI Team Center",
    short: "AI",
    icon: "🤖",
    route: "/platform-builder/ai-team",
    x: 78,
    y: 22,
    w: 14,
    h: 15,
    district: "intel",
    searchTokens: ["ai", "team", "agents", "copilot"],
  },
  {
    id: "knowledge",
    label: "Knowledge Center",
    short: "KB",
    icon: "📚",
    route: "/platform-builder/knowledge",
    x: 64,
    y: 48,
    w: 13,
    h: 13,
    district: "intel",
    searchTokens: ["knowledge", "kb", "wiki"],
  },
  {
    id: "documents",
    label: "Documents",
    short: "Docs",
    icon: "📄",
    route: "/workspace/docs",
    x: 78,
    y: 52,
    w: 12,
    h: 12,
    district: "intel",
    searchTokens: ["documents", "docs", "files"],
  },
  {
    id: "production",
    label: "Production",
    short: "Prod",
    icon: "⚙",
    route: "/workspace/drone",
    x: 8,
    y: 72,
    w: 14,
    h: 14,
    district: "ops",
    searchTokens: ["production", "drone", "fleet", "ops"],
  },
  {
    id: "mission_control",
    label: "Mission Control",
    short: "MC",
    icon: "🎛",
    route: "/platform-builder/mission-control",
    x: 26,
    y: 74,
    w: 14,
    h: 14,
    district: "ops",
    searchTokens: ["mission", "control", "ops", "live"],
  },
  {
    id: "hr",
    label: "HR",
    short: "HR",
    icon: "👥",
    route: "/workspace/hr",
    x: 48,
    y: 68,
    w: 12,
    h: 12,
    district: "people",
    searchTokens: ["hr", "people", "employees", "staff"],
  },
  {
    id: "admin",
    label: "Administration",
    short: "Admin",
    icon: "🏛",
    route: "/settings",
    x: 64,
    y: 72,
    w: 13,
    h: 13,
    district: "people",
    searchTokens: ["admin", "settings", "administration"],
  },
  {
    id: "dashboard",
    label: "Command Center",
    short: "Dash",
    icon: "◻",
    route: "/dashboard",
    x: 46,
    y: 18,
    w: 12,
    h: 12,
    district: "hub",
    searchTokens: ["dashboard", "command", "center"],
  },
  {
    id: "concierge",
    label: "AI Concierge",
    short: "AI-C",
    icon: "✨",
    route: "/platform-builder/concierge",
    x: 82,
    y: 72,
    w: 12,
    h: 12,
    district: "intel",
    searchTokens: ["concierge", "assistant"],
  },
];

export type CityLiveStatus = {
  tone: CityActivityTone;
  notifications: number;
  tasks: number;
  aiActive: boolean;
  processLabel: string;
};

/** Seed live overlay — client-side only; enriched by useCityLiveStatus. */
export const CITY_STATUS_SEED: Record<CityBuildingId, CityLiveStatus> = {
  hub: { tone: "active", notifications: 2, tasks: 3, aiActive: false, processLabel: "Workspace sync" },
  crm: { tone: "busy", notifications: 5, tasks: 8, aiActive: true, processLabel: "Pipeline updates" },
  sales: { tone: "active", notifications: 1, tasks: 4, aiActive: true, processLabel: "Follow-ups" },
  marketing: { tone: "idle", notifications: 0, tasks: 1, aiActive: false, processLabel: "Idle" },
  finance: { tone: "active", notifications: 2, tasks: 2, aiActive: false, processLabel: "Closing" },
  analytics: { tone: "active", notifications: 0, tasks: 0, aiActive: true, processLabel: "Insights" },
  ai_team: { tone: "busy", notifications: 3, tasks: 6, aiActive: true, processLabel: "Agents running" },
  knowledge: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Stable" },
  documents: { tone: "active", notifications: 1, tasks: 2, aiActive: false, processLabel: "Reviews" },
  production: { tone: "active", notifications: 2, tasks: 3, aiActive: true, processLabel: "Fleet OK" },
  mission_control: { tone: "busy", notifications: 4, tasks: 5, aiActive: true, processLabel: "Live ops" },
  hr: { tone: "idle", notifications: 0, tasks: 1, aiActive: false, processLabel: "Quiet" },
  admin: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Config" },
  dashboard: { tone: "active", notifications: 0, tasks: 0, aiActive: false, processLabel: "Command" },
  concierge: { tone: "active", notifications: 1, tasks: 2, aiActive: true, processLabel: "Briefing" },
};

export function getBuilding(id: CityBuildingId): CityBuilding | undefined {
  return CITY_BUILDINGS.find((b) => b.id === id);
}

export function searchBuildings(query: string): CityBuilding[] {
  const q = query.trim().toLowerCase();
  if (!q) return CITY_BUILDINGS;
  return CITY_BUILDINGS.filter((b) => {
    const hay = `${b.label} ${b.short} ${b.searchTokens.join(" ")} ${b.route}`.toLowerCase();
    return hay.includes(q);
  });
}
