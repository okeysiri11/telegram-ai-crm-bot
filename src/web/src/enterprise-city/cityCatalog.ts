/**
 * Enterprise City catalog — Sprint 32.3.3 / 27.8.
 * Visual navigation only: each building opens an existing route.
 * No business logic / duplicated pages.
 */

export type CityBuildingId =
  | "hub"
  | "plaza"
  | "crm"
  | "sales"
  | "marketing"
  | "erp"
  | "finance"
  | "analytics"
  | "ai_team"
  | "ai_studio"
  | "knowledge"
  | "documents"
  | "production"
  | "prod_image"
  | "prod_video"
  | "prod_audio"
  | "prod_voice"
  | "prod_avatar"
  | "prod_reels"
  | "prod_ads"
  | "prod_creative"
  | "prod_prompt"
  | "prod_brand"
  | "prod_publish"
  | "prod_analytics"
  | "prod_render"
  | "prod_assets"
  | "prod_templates"
  | "prod_media"
  | "mission_control"
  | "marketplace"
  | "hr"
  | "admin"
  | "dashboard"
  | "concierge"
  | "developer"
  | "security"
  | "settings"
  | "business_network"
  | "digital_citizens"
  | "warehouse"
  | "legal"
  | "casino";

/** Sprint 30.4 navigation districts (primary city map). */
export type CityDistrictId =
  | "enterprise"
  | "crm"
  | "erp"
  | "ai"
  | "production"
  | "marketplace"
  | "analytics"
  | "knowledge"
  | "finance"
  | "developer"
  | "security"
  | "settings"
  | "warehouse"
  | "legal"
  | "marketing"
  | "documents";

export type CityActivityTone = "idle" | "active" | "busy" | "alert";

export type CityBuilding = {
  id: CityBuildingId;
  label: string;
  short: string;
  icon: string;
  /** Existing platform route only — never a duplicated page. */
  route: string;
  /** Map coordinates in 0–100 space (percent of city plane). */
  x: number;
  y: number;
  w: number;
  h: number;
  district: CityDistrictId;
  searchTokens: string[];
  /** Optional AI assistant label (reuses Concierge / Agents routes). */
  aiAssistant?: string;
  kind?: "building" | "plaza";
};

/** Buildings → existing Workspace / Shell / Platform Builder pages. */
export const CITY_BUILDINGS: CityBuilding[] = [
  {
    id: "plaza",
    label: "Central Plaza",
    short: "Plaza",
    icon: "◇",
    route: "/enterprise-city",
    x: 42,
    y: 40,
    w: 16,
    h: 14,
    district: "enterprise",
    kind: "plaza",
    searchTokens: ["plaza", "square", "center", "навигация", "город"],
    aiAssistant: "City Concierge",
  },
  {
    id: "hub",
    label: "Enterprise Hub",
    short: "Hub",
    icon: "◉",
    route: "/workspace",
    x: 44,
    y: 24,
    w: 12,
    h: 12,
    district: "enterprise",
    searchTokens: ["hub", "enterprise", "workspace", "home"],
    aiAssistant: "Enterprise Advisor",
  },
  {
    id: "dashboard",
    label: "Command Center",
    short: "Dash",
    icon: "◻",
    route: "/dashboard",
    x: 58,
    y: 22,
    w: 11,
    h: 11,
    district: "enterprise",
    searchTokens: ["dashboard", "command", "center"],
    aiAssistant: "Ops Advisor",
  },
  {
    id: "crm",
    label: "CRM Center",
    short: "CRM",
    icon: "▣",
    route: "/crm",
    x: 10,
    y: 18,
    w: 13,
    h: 13,
    district: "crm",
    searchTokens: ["crm", "clients", "pipeline"],
    aiAssistant: "CRM Copilot",
  },
  {
    id: "sales",
    label: "Sales",
    short: "Sales",
    icon: "▵",
    route: "/crm",
    x: 24,
    y: 14,
    w: 11,
    h: 11,
    district: "crm",
    searchTokens: ["sales", "deals", "funnel"],
    aiAssistant: "Sales Agent",
  },
  {
    id: "marketing",
    label: "Marketing Center",
    short: "Mkt",
    icon: "◈",
    route: "/production-studio?studio=ads",
    x: 8,
    y: 52,
    w: 11,
    h: 11,
    district: "marketing",
    searchTokens: ["marketing", "campaigns", "growth", "маркетинг"],
    aiAssistant: "Growth Agent",
  },
  {
    id: "erp",
    label: "ERP Center",
    short: "ERP",
    icon: "▦",
    route: "/erp",
    x: 26,
    y: 38,
    w: 13,
    h: 13,
    district: "erp",
    searchTokens: ["erp", "operations", "inventory", "supply"],
    aiAssistant: "ERP Advisor",
  },
  {
    id: "finance",
    label: "Finance",
    short: "Fin",
    icon: "◈",
    route: "/workspace/finance",
    x: 28,
    y: 56,
    w: 12,
    h: 12,
    district: "finance",
    searchTokens: ["finance", "billing", "treasury", "money", "финансы"],
    aiAssistant: "Finance Agent",
  },
  {
    id: "analytics",
    label: "Analytics Center",
    short: "BI",
    icon: "▤",
    route: "/analytics",
    x: 64,
    y: 12,
    w: 13,
    h: 13,
    district: "analytics",
    searchTokens: ["analytics", "intelligence", "kpi", "reports"],
    aiAssistant: "Insights Agent",
  },
  {
    id: "ai_team",
    label: "AI Team Center",
    short: "AI",
    icon: "◎",
    route: "/ai-agents",
    x: 80,
    y: 16,
    w: 13,
    h: 13,
    district: "ai",
    searchTokens: ["ai", "team", "agents", "copilot"],
    aiAssistant: "Agent Supervisor",
  },
  {
    id: "ai_studio",
    label: "Студия AI",
    short: "Studio",
    icon: "✦",
    route: "/ai-studio",
    x: 78,
    y: 34,
    w: 12,
    h: 12,
    district: "ai",
    searchTokens: ["ai", "studio", "image", "video", "voice", "avatar", "prompt", "generate"],
    aiAssistant: "Studio Guide",
  },
  {
    id: "concierge",
    label: "AI Concierge",
    short: "AI-C",
    icon: "✧",
    route: "/platform-builder/concierge",
    x: 66,
    y: 34,
    w: 11,
    h: 11,
    district: "ai",
    searchTokens: ["concierge", "assistant", "advisor"],
    aiAssistant: "Executive Concierge",
  },
  {
    id: "knowledge",
    label: "Knowledge Center",
    short: "KB",
    icon: "▤",
    route: "/knowledge",
    x: 64,
    y: 52,
    w: 12,
    h: 12,
    district: "knowledge",
    searchTokens: ["knowledge", "kb", "wiki"],
    aiAssistant: "Knowledge Agent",
  },
  {
    id: "documents",
    label: "Documents Center",
    short: "Docs",
    icon: "▥",
    route: "/documents",
    x: 88,
    y: 48,
    w: 11,
    h: 11,
    district: "documents",
    searchTokens: ["documents", "docs", "files", "документы"],
    aiAssistant: "Docs Agent",
  },
  {
    id: "production",
    label: "AI Production Center",
    short: "Prod",
    icon: "⚙",
    route: "/production-studio",
    x: 6,
    y: 62,
    w: 12,
    h: 12,
    district: "production",
    searchTokens: ["production", "studio", "creative", "reels", "render"],
    aiAssistant: "Production Director",
  },
  {
    id: "prod_image",
    label: "Студия изображений",
    short: "Img",
    icon: "▣",
    route: "/production-studio?studio=image",
    x: 18,
    y: 58,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["image", "photo", "still"],
    aiAssistant: "Creative Director",
  },
  {
    id: "prod_video",
    label: "Студия видео",
    short: "Vid",
    icon: "▤",
    route: "/production-studio?studio=video",
    x: 28,
    y: 58,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["video", "film", "clip"],
    aiAssistant: "Video Director",
  },
  {
    id: "prod_audio",
    label: "Студия аудио",
    short: "Audio",
    icon: "♪",
    route: "/production-studio?studio=audio",
    x: 38,
    y: 58,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["audio", "sfx", "mix", "sound"],
    aiAssistant: "Audio Agent",
  },
  {
    id: "prod_voice",
    label: "Голосовая студия",
    short: "Voice",
    icon: "◉",
    route: "/production-studio?studio=voice",
    x: 38,
    y: 68,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["voice", "tts", "narration"],
    aiAssistant: "Voice Agent",
  },
  {
    id: "prod_avatar",
    label: "Avatar Studio",
    short: "Avatar",
    icon: "☺",
    route: "/production-studio?studio=avatar",
    x: 46,
    y: 62,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["avatar", "presenter", "lipsync"],
    aiAssistant: "Avatar Agent",
  },
  {
    id: "prod_reels",
    label: "Reels Factory",
    short: "Reels",
    icon: "◈",
    route: "/production-studio?studio=reels",
    x: 18,
    y: 70,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["reels", "shorts", "tiktok"],
    aiAssistant: "Reels Agent",
  },
  {
    id: "prod_ads",
    label: "Ads Factory",
    short: "Ads",
    icon: "◇",
    route: "/production-studio?studio=ads",
    x: 28,
    y: 70,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["ads", "paid", "campaign"],
    aiAssistant: "Ads Agent",
  },
  {
    id: "prod_creative",
    label: "Creative Studio",
    short: "Creative",
    icon: "✧",
    route: "/production-studio?studio=creative",
    x: 8,
    y: 68,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["creative", "campaign", "brief", "board"],
    aiAssistant: "Creative Director",
  },
  {
    id: "prod_prompt",
    label: "Студия промптов",
    short: "Prompt",
    icon: "✦",
    route: "/production-studio?tab=prompts",
    x: 6,
    y: 76,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["prompt", "library", "creative"],
    aiAssistant: "Prompt Engineer",
  },
  {
    id: "prod_brand",
    label: "Brand Studio",
    short: "Brand",
    icon: "◎",
    route: "/production-studio?studio=brand",
    x: 16,
    y: 82,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["brand", "kit", "tone"],
    aiAssistant: "Brand Compliance",
  },
  {
    id: "prod_publish",
    label: "Publishing Center",
    short: "Pub",
    icon: "⬡",
    route: "/production-studio?studio=publishing",
    x: 26,
    y: 82,
    w: 9,
    h: 9,
    district: "production",
    searchTokens: ["publish", "channels", "schedule"],
    aiAssistant: "Publisher",
  },
  {
    id: "prod_render",
    label: "Render Center",
    short: "Render",
    icon: "▣",
    route: "/production-studio?studio=render&tab=runtime",
    x: 36,
    y: 84,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["render", "queue", "farm"],
    aiAssistant: "Render Orchestrator",
  },
  {
    id: "prod_analytics",
    label: "Analytics",
    short: "Analyt",
    icon: "▤",
    route: "/production-studio?studio=analytics",
    x: 46,
    y: 76,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["analytics", "reach", "creative performance", "production analytics"],
    aiAssistant: "Insights Agent",
  },
  {
    id: "prod_assets",
    label: "Asset Library",
    short: "Assets",
    icon: "▥",
    route: "/ai-studio?tab=assets",
    x: 54,
    y: 70,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["assets", "library", "brand assets"],
    aiAssistant: "Asset Librarian",
  },
  {
    id: "prod_templates",
    label: "Template Library",
    short: "Tpl",
    icon: "▦",
    route: "/ai-studio?tab=templates",
    x: 54,
    y: 80,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["templates", "template library"],
    aiAssistant: "Template Agent",
  },
  {
    id: "prod_media",
    label: "Media Browser",
    short: "Media",
    icon: "▧",
    route: "/ai-studio?tab=media",
    x: 62,
    y: 74,
    w: 8,
    h: 8,
    district: "production",
    searchTokens: ["media", "browser", "gallery"],
    aiAssistant: "Media Agent",
  },
  {
    id: "mission_control",
    label: "Mission Control",
    short: "MC",
    icon: "▣",
    route: "/platform-builder/mission-control",
    x: 36,
    y: 76,
    w: 10,
    h: 10,
    district: "production",
    searchTokens: ["mission", "control", "ops", "live"],
    aiAssistant: "Ops Copilot",
  },
  {
    id: "marketplace",
    label: "Marketplace",
    short: "Market",
    icon: "◇",
    route: "/marketplace",
    x: 40,
    y: 68,
    w: 13,
    h: 13,
    district: "marketplace",
    searchTokens: ["marketplace", "apps", "store", "plugins"],
    aiAssistant: "Marketplace Guide",
  },
  {
    id: "business_network",
    label: "Business Network",
    short: "EBN",
    icon: "⬡",
    route: "/business-network",
    x: 28,
    y: 72,
    w: 12,
    h: 11,
    district: "marketplace",
    searchTokens: ["business", "network", "partner", "supplier", "ebn", "relationship"],
    aiAssistant: "Network Advisor",
  },
  {
    id: "digital_citizens",
    label: "Цифровые граждане",
    short: "People",
    icon: "◎",
    route: "/digital-citizens",
    x: 16,
    y: 70,
    w: 11,
    h: 11,
    district: "enterprise",
    searchTokens: ["citizen", "people", "presence", "hr", "employee", "digital"],
    aiAssistant: "People Advisor",
  },
  {
    id: "hr",
    label: "HR",
    short: "HR",
    icon: "◎",
    route: "/identity/users",
    x: 54,
    y: 70,
    w: 11,
    h: 11,
    district: "enterprise",
    searchTokens: ["hr", "people", "employees", "staff"],
    aiAssistant: "People Agent",
  },
  {
    id: "developer",
    label: "Developer Tools",
    short: "Dev",
    icon: "⬡",
    route: "/command-center",
    x: 68,
    y: 70,
    w: 12,
    h: 12,
    district: "developer",
    searchTokens: ["developer", "devtools", "command", "palette"],
    aiAssistant: "Dev Copilot",
  },
  {
    id: "security",
    label: "Security Center",
    short: "Sec",
    icon: "⬡",
    route: "/identity/security",
    x: 82,
    y: 70,
    w: 12,
    h: 12,
    district: "security",
    searchTokens: ["security", "identity", "access", "audit"],
    aiAssistant: "Security Agent",
  },
  {
    id: "settings",
    label: "Settings",
    short: "Set",
    icon: "◍",
    route: "/settings",
    x: 82,
    y: 86,
    w: 11,
    h: 10,
    district: "settings",
    searchTokens: ["settings", "preferences", "config"],
    aiAssistant: "Config Assistant",
  },
  {
    id: "admin",
    label: "Administration",
    short: "Admin",
    icon: "▣",
    route: "/settings",
    x: 68,
    y: 86,
    w: 11,
    h: 10,
    district: "settings",
    searchTokens: ["admin", "administration", "tenant", "администрация"],
    aiAssistant: "Admin Advisor",
  },
  {
    id: "warehouse",
    label: "Warehouse",
    short: "Wh",
    icon: "▦",
    route: "/erp?view=warehouse",
    x: 38,
    y: 46,
    w: 11,
    h: 11,
    district: "warehouse",
    searchTokens: ["warehouse", "склад", "inventory", "stock"],
    aiAssistant: "Warehouse Advisor",
  },
  {
    id: "legal",
    label: "Legal Center",
    short: "Legal",
    icon: "▣",
    route: "/workspace/legal",
    x: 58,
    y: 86,
    w: 11,
    h: 10,
    district: "legal",
    searchTokens: ["legal", "юридический", "contracts", "law"],
    aiAssistant: "Legal Advisor",
  },
  {
    id: "casino",
    label: "Odessa Prime Casino",
    short: "Casino",
    icon: "◈",
    route: "/casino",
    x: 50,
    y: 78,
    w: 12,
    h: 11,
    district: "marketplace",
    searchTokens: ["casino", "roulette", "venue", "odessa", "prime", "play", "chips", "казино", "рулетка", "демо"],
    aiAssistant: "Casino Concierge",
  },
];

export type CityLiveStatus = {
  tone: CityActivityTone;
  notifications: number;
  tasks: number;
  aiActive: boolean;
  processLabel: string;
};

const defaultStatus = (label: string, tone: CityActivityTone = "idle"): CityLiveStatus => ({
  tone,
  notifications: 0,
  tasks: 0,
  aiActive: false,
  processLabel: label,
});

/** Seed live overlay — client-side only; enriched by useCityLiveStatus. */
export const CITY_STATUS_SEED: Record<CityBuildingId, CityLiveStatus> = {
  plaza: { tone: "active", notifications: 0, tasks: 0, aiActive: true, processLabel: "Welcome" },
  hub: { tone: "active", notifications: 2, tasks: 3, aiActive: false, processLabel: "Workspace sync" },
  crm: { tone: "busy", notifications: 5, tasks: 8, aiActive: true, processLabel: "Pipeline updates" },
  sales: { tone: "active", notifications: 1, tasks: 4, aiActive: true, processLabel: "Follow-ups" },
  marketing: { tone: "idle", notifications: 0, tasks: 1, aiActive: false, processLabel: "Idle" },
  erp: { tone: "active", notifications: 1, tasks: 3, aiActive: true, processLabel: "Supply sync" },
  finance: { tone: "active", notifications: 2, tasks: 2, aiActive: false, processLabel: "Closing" },
  analytics: { tone: "active", notifications: 0, tasks: 0, aiActive: true, processLabel: "Insights" },
  ai_team: { tone: "busy", notifications: 3, tasks: 6, aiActive: true, processLabel: "Agents running" },
  ai_studio: { tone: "active", notifications: 1, tasks: 2, aiActive: true, processLabel: "Studio ready" },
  knowledge: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Stable" },
  documents: { tone: "active", notifications: 1, tasks: 2, aiActive: false, processLabel: "Reviews" },
  production: { tone: "active", notifications: 2, tasks: 3, aiActive: true, processLabel: "Projects OK" },
  prod_image: { tone: "active", notifications: 0, tasks: 1, aiActive: true, processLabel: "Variants" },
  prod_video: { tone: "busy", notifications: 1, tasks: 2, aiActive: true, processLabel: "Timeline" },
  prod_audio: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Mix ready" },
  prod_voice: { tone: "active", notifications: 0, tasks: 1, aiActive: true, processLabel: "TTS" },
  prod_avatar: { tone: "idle", notifications: 0, tasks: 0, aiActive: true, processLabel: "Lip-sync" },
  prod_reels: { tone: "busy", notifications: 2, tasks: 4, aiActive: true, processLabel: "Hooks" },
  prod_ads: { tone: "active", notifications: 1, tasks: 2, aiActive: true, processLabel: "A/B pack" },
  prod_creative: { tone: "active", notifications: 0, tasks: 1, aiActive: true, processLabel: "Brief" },
  prod_prompt: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Library" },
  prod_brand: { tone: "idle", notifications: 0, tasks: 0, aiActive: true, processLabel: "Guarded" },
  prod_publish: { tone: "active", notifications: 1, tasks: 1, aiActive: false, processLabel: "Approval gate" },
  prod_render: { tone: "busy", notifications: 1, tasks: 3, aiActive: true, processLabel: "Farm" },
  prod_analytics: { tone: "active", notifications: 0, tasks: 1, aiActive: true, processLabel: "Reach" },
  prod_assets: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Library" },
  prod_templates: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Templates" },
  prod_media: { tone: "active", notifications: 0, tasks: 1, aiActive: false, processLabel: "Browser" },
  mission_control: { tone: "busy", notifications: 4, tasks: 5, aiActive: true, processLabel: "Live ops" },
  marketplace: { tone: "active", notifications: 1, tasks: 1, aiActive: false, processLabel: "Catalog" },
  business_network: { tone: "active", notifications: 1, tasks: 2, aiActive: false, processLabel: "Partners" },
  digital_citizens: { tone: "active", notifications: 2, tasks: 3, aiActive: true, processLabel: "Presence" },
  hr: { tone: "idle", notifications: 0, tasks: 1, aiActive: false, processLabel: "Quiet" },
  admin: { tone: "idle", notifications: 0, tasks: 0, aiActive: false, processLabel: "Config" },
  dashboard: { tone: "active", notifications: 0, tasks: 0, aiActive: false, processLabel: "Command" },
  concierge: { tone: "active", notifications: 1, tasks: 2, aiActive: true, processLabel: "Briefing" },
  developer: { tone: "active", notifications: 0, tasks: 1, aiActive: true, processLabel: "Tools online" },
  security: { tone: "idle", notifications: 0, tasks: 0, aiActive: true, processLabel: "Guarded" },
  settings: defaultStatus("Preferences"),
  warehouse: { tone: "active", notifications: 1, tasks: 2, aiActive: false, processLabel: "Stock sync" },
  legal: { tone: "idle", notifications: 0, tasks: 1, aiActive: false, processLabel: "Contracts" },
  casino: { tone: "active", notifications: 0, tasks: 1, aiActive: false, processLabel: "Play-money floor" },
};

export function getBuilding(id: CityBuildingId): CityBuilding | undefined {
  return CITY_BUILDINGS.find((b) => b.id === id);
}

export function buildingsByDistrict(district: CityDistrictId): CityBuilding[] {
  return CITY_BUILDINGS.filter((b) => b.district === district);
}

export function searchBuildings(query: string): CityBuilding[] {
  const q = query.trim().toLowerCase();
  if (!q) return CITY_BUILDINGS;
  return CITY_BUILDINGS.filter((b) => {
    const hay = `${b.label} ${b.short} ${b.district} ${b.searchTokens.join(" ")} ${b.route} ${b.aiAssistant || ""}`.toLowerCase();
    return hay.includes(q);
  });
}
