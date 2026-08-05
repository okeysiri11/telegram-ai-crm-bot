/**
 * Enterprise Integration Hub — Sprint 28.0.
 * Shared context · event bus · session restore · deep links · search registration.
 * Extends existing stores — no parallel auth/search/notification engines.
 */

export const INTEGRATION_HUB_VERSION = "28.0";
export const INTEGRATION_BOOT_KEY = "ews_integration_boot_v1";

export type OsSurfaceId =
  | "desktop"
  | "dashboard"
  | "workspace"
  | "city"
  | "production"
  | "command_center"
  | "crm"
  | "settings"
  | "devtools"
  | "other";

export type EnterpriseEventType =
  | "navigate"
  | "open_module"
  | "open_city_building"
  | "open_production"
  | "ai_request"
  | "job_update"
  | "runtime_update"
  | "notification"
  | "context_changed"
  | "session_restored"
  | "workflow_update"
  | "provider_update"
  | "desktop_update"
  | "city_update"
  | "command.started"
  | "command.completed"
  | "command.failed"
  | "command.cancelled"
  | "business_network_update"
  | "digital_citizen_update"
  | "life_engine_update"
  | "asset_runtime_update"
  | "spatial_runtime_update"
  | "city_visualization_update"
  | "interaction_runtime_update"
  | "intelligence_runtime_update"
  | "orchestrator_runtime_update"
  | "kernel_runtime_update";

export type EnterpriseEvent = {
  type: EnterpriseEventType;
  source: OsSurfaceId | "system" | "hub";
  path?: string;
  payload?: Record<string, unknown>;
  at: string;
};

export type SharedAppContext = {
  workspaceId: string;
  userId: string | null;
  userName: string | null;
  organization: string;
  project: string;
  moduleId: string;
  surface: OsSurfaceId;
  aiSessionId: string | null;
  runtimeLabel: string;
  profileId: string;
  path: string;
};

export type DeepLinkTarget = {
  id: string;
  label: string;
  path: string;
  surface: OsSurfaceId;
  tokens: string[];
};

/** Canonical OS surfaces — SPA routes (no full reload). */
export const OS_DEEP_LINKS: DeepLinkTarget[] = [
  { id: "desktop", label: "Enterprise Desktop", path: "/desktop", surface: "desktop", tokens: ["desktop", "os", "dock"] },
  { id: "dashboard", label: "Dashboard", path: "/dashboard", surface: "dashboard", tokens: ["dashboard", "command", "brief"] },
  { id: "workspace", label: "Workspace", path: "/workspace", surface: "workspace", tokens: ["workspace", "tabs"] },
  { id: "city", label: "Enterprise City", path: "/enterprise-city", surface: "city", tokens: ["city", "map", "district"] },
  { id: "production", label: "Production Studio", path: "/production-studio", surface: "production", tokens: ["production", "studio", "reels"] },
  { id: "command_center", label: "Command Center", path: "/command-center", surface: "command_center", tokens: ["command", "palette", "devtools"] },
  { id: "crm", label: "CRM", path: "/crm", surface: "crm", tokens: ["crm", "clients", "pipeline"] },
  { id: "settings", label: "Settings", path: "/settings", surface: "settings", tokens: ["settings", "prefs"] },
  { id: "devtools", label: "Developer Tools", path: "/command-center", surface: "devtools", tokens: ["developer", "tools"] },
  { id: "search", label: "Universal Search", path: "/search", surface: "other", tokens: ["search", "find"] },
  { id: "knowledge", label: "Knowledge", path: "/knowledge", surface: "other", tokens: ["knowledge", "kb"] },
  { id: "documents", label: "Documents", path: "/documents", surface: "other", tokens: ["documents", "docs"] },
  { id: "ai_agents", label: "AI Agents", path: "/ai-agents", surface: "other", tokens: ["agents", "ai"] },
];

export function surfaceFromPath(pathname: string): OsSurfaceId {
  const p = pathname.split("?")[0] || pathname;
  if (p.startsWith("/desktop")) return "desktop";
  if (p.startsWith("/dashboard")) return "dashboard";
  if (p.startsWith("/workspace")) return "workspace";
  if (p.startsWith("/enterprise-city") || p === "/city") return "city";
  if (p.startsWith("/production")) return "production";
  if (p.startsWith("/command-center")) return "command_center";
  if (p.startsWith("/crm")) return "crm";
  if (p.startsWith("/settings")) return "settings";
  return "other";
}

export function buildDeepLink(opts: {
  surface?: OsSurfaceId;
  path?: string;
  studio?: string;
  tab?: string;
  building?: string;
  mode?: string;
  embed?: boolean;
  q?: string;
}): string {
  let base = opts.path || "/dashboard";
  if (opts.surface) {
    const hit = OS_DEEP_LINKS.find((d) => d.surface === opts.surface && d.id === opts.surface);
    if (hit) base = hit.path;
  }
  const [pathOnly, existing] = base.split("?");
  const params = new URLSearchParams(existing || "");
  if (opts.studio) params.set("studio", opts.studio);
  if (opts.tab) params.set("tab", opts.tab);
  if (opts.building) params.set("building", opts.building);
  if (opts.mode) params.set("mode", opts.mode);
  if (opts.embed) params.set("embed", "1");
  if (opts.q) params.set("q", opts.q);
  const qs = params.toString();
  return qs ? `${pathOnly}?${qs}` : pathOnly!;
}

export function parseDeepLink(url: string): {
  path: string;
  studio?: string;
  tab?: string;
  building?: string;
  mode?: string;
  embed: boolean;
  q?: string;
} {
  try {
    const u = url.startsWith("http") ? new URL(url) : new URL(url, "http://local");
    return {
      path: u.pathname,
      studio: u.searchParams.get("studio") || undefined,
      tab: u.searchParams.get("tab") || undefined,
      building: u.searchParams.get("building") || undefined,
      mode: u.searchParams.get("mode") || undefined,
      embed: u.searchParams.get("embed") === "1",
      q: u.searchParams.get("q") || undefined,
    };
  } catch {
    return { path: url.split("?")[0] || url, embed: false };
  }
}
