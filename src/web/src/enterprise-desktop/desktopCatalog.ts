import type { DesktopAppDef, DesktopIcon, DesktopLayoutId, DockItem, WallpaperId } from "./types";

export const WALLPAPERS: Record<WallpaperId, { label: string; css: string }> = {
  aurora: {
    label: "Aurora",
    css: "radial-gradient(1200px 600px at 10% 0%, color-mix(in oklab, var(--eds-primary) 28%, transparent), transparent 60%), radial-gradient(900px 500px at 90% 20%, color-mix(in oklab, #3d7ea6 22%, transparent), transparent 55%), linear-gradient(160deg, #0f1419 0%, #1a2330 50%, #121820 100%)",
  },
  slate: {
    label: "Slate",
    css: "linear-gradient(145deg, #1c222b 0%, #2a3340 45%, #171c24 100%)",
  },
  studio: {
    label: "Studio",
    css: "radial-gradient(800px 400px at 50% 0%, color-mix(in oklab, var(--eds-primary) 18%, transparent), transparent 70%), linear-gradient(180deg, #141820 0%, #0e1218 100%)",
  },
  midnight: {
    label: "Midnight",
    css: "linear-gradient(180deg, #0a0d12 0%, #121826 60%, #0b1018 100%)",
  },
  plain: {
    label: "Plain",
    css: "var(--eds-bg)",
  },
};

/** Launcher + dock application catalog. */
export const DESKTOP_APPS: DesktopAppDef[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: "dashboard", group: "core", badgeKey: "notifications" },
  { id: "crm", label: "CRM", path: "/crm", icon: "crm", group: "core" },
  { id: "erp", label: "ERP", path: "/erp", icon: "erp", group: "core" },
  { id: "finance", label: "Finance", path: "/analytics", icon: "analytics", group: "core" },
  { id: "knowledge", label: "Knowledge", path: "/knowledge", icon: "knowledge", group: "core" },
  { id: "ai_studio", label: "AI Studio", path: "/ai-studio", icon: "ai_studio", group: "ai", badgeKey: "ai" },
  { id: "ai_agents", label: "AI Agents", path: "/ai-agents", icon: "ai_agents", group: "ai", badgeKey: "ai" },
  { id: "marketplace", label: "Marketplace", path: "/marketplace", icon: "marketplace", group: "ops" },
  { id: "analytics", label: "Analytics", path: "/analytics", icon: "analytics", group: "ops" },
  { id: "settings", label: "Settings", path: "/settings", icon: "settings", group: "tools" },
  { id: "city", label: "Enterprise City", path: "/enterprise-city", icon: "city", group: "ops" },
  { id: "production", label: "Production Studio", path: "/production-studio", icon: "projects", group: "ops", badgeKey: "jobs" },
  { id: "prod_image", label: "Image Studio", path: "/production-studio?studio=image", icon: "projects", group: "ops" },
  { id: "prod_video", label: "Video Studio", path: "/production-studio?studio=video", icon: "projects", group: "ops" },
  { id: "prod_audio", label: "Audio Studio", path: "/production-studio?studio=audio", icon: "projects", group: "ops" },
  { id: "prod_voice", label: "Voice Studio", path: "/production-studio?studio=voice", icon: "projects", group: "ops" },
  { id: "prod_avatar", label: "Avatar Studio", path: "/ai-studio?studio=avatar", icon: "projects", group: "ops" },
  { id: "prod_reels", label: "Reels Factory", path: "/production-studio?studio=reels", icon: "projects", group: "ops" },
  { id: "prod_ads", label: "Ads Factory", path: "/production-studio?studio=ads", icon: "projects", group: "ops" },
  { id: "prod_creative", label: "Creative Studio", path: "/production-studio?studio=creative", icon: "projects", group: "ops" },
  { id: "prod_prompt", label: "Prompt Studio", path: "/production-studio?tab=prompts", icon: "ai_studio", group: "ai" },
  { id: "prod_publish", label: "Publishing Center", path: "/production-studio?studio=publishing", icon: "projects", group: "ops" },
  { id: "prod_runtime", label: "Production Runtime", path: "/production-studio?tab=runtime", icon: "automation", group: "ops", badgeKey: "jobs" },
  { id: "prod_analytics", label: "Production Analytics", path: "/production-studio?studio=analytics", icon: "analytics", group: "ops" },
  { id: "workflow_studio", label: "Workflow Studio", path: "/platform-builder/workflow-center", icon: "automation", group: "ops", badgeKey: "jobs" },
  { id: "agent_studio", label: "Agent Studio", path: "/platform-builder/builder-studio", icon: "ai_agents", group: "ai", badgeKey: "ai" },
  { id: "devtools", label: "Developer Tools", path: "/command-center", icon: "integrations", group: "tools" },
  { id: "cmd_runtime", label: "Command Inspector", path: "/command-runtime", icon: "integrations", group: "tools" },
  { id: "workflow_runtime", label: "Workflow Runtime", path: "/workflow-runtime", icon: "automation", group: "tools" },
  { id: "automation_center", label: "Automation Center", path: "/automation", icon: "automation", group: "tools" },
  { id: "business_network", label: "Business Network", path: "/business-network", icon: "marketplace", group: "core" },
  { id: "digital_citizens", label: "Digital Citizens", path: "/digital-citizens", icon: "hr", group: "core" },
  { id: "life_engine", label: "Life Engine", path: "/life-engine", icon: "city", group: "ops" },
  { id: "assets", label: "Asset Runtime", path: "/assets", icon: "erp", group: "ops" },
  { id: "spatial", label: "Spatial Runtime", path: "/spatial", icon: "city", group: "ops" },
  { id: "city_visualization", label: "City Visualization", path: "/city-visualization", icon: "city", group: "ops" },
  { id: "interactions", label: "Interaction Runtime", path: "/interactions", icon: "city", group: "ops" },
  { id: "intelligence", label: "Intelligence Runtime", path: "/intelligence", icon: "analytics", group: "ops" },
  { id: "orchestrator", label: "Orchestrator", path: "/orchestrator", icon: "integrations", group: "tools" },
  { id: "kernel", label: "Enterprise Kernel", path: "/kernel", icon: "integrations", group: "tools" },
  { id: "documents", label: "Documents", path: "/documents", icon: "documents", group: "core" },
  { id: "automation", label: "Automation", path: "/automation", icon: "automation", group: "ops", badgeKey: "jobs" },
];

export function appById(id: string): DesktopAppDef | undefined {
  return DESKTOP_APPS.find((a) => a.id === id);
}

export function appByPath(path: string): DesktopAppDef | undefined {
  const clean = path.split("?")[0] || path;
  return DESKTOP_APPS.find((a) => a.path === clean || clean.startsWith(a.path + "/"));
}

const DEFAULT_DOCK: DockItem[] = [
  { appId: "dashboard", pinned: true },
  { appId: "city", pinned: true },
  { appId: "crm", pinned: true },
  { appId: "ai_studio", pinned: true },
  { appId: "knowledge", pinned: true },
  { appId: "settings", pinned: true },
];

function iconGrid(layout: DesktopLayoutId): DesktopIcon[] {
  const apps =
    layout === "sales"
      ? ["crm", "analytics", "dashboard", "documents", "ai_agents"]
      : layout === "ops"
        ? ["dashboard", "erp", "production", "automation", "ai_studio", "marketplace"]
        : layout === "dev"
          ? ["devtools", "ai_studio", "dashboard", "settings", "automation"]
          : ["dashboard", "crm", "erp", "knowledge", "ai_studio", "marketplace", "settings", "city"];

  const icons: DesktopIcon[] = apps.map((id, i) => {
    const app = appById(id)!;
    return {
      id: `icon_${id}`,
      label: app.label,
      kind: "app" as const,
      target: app.path,
      x: 24 + (i % 2) * 100,
      y: 24 + Math.floor(i / 2) * 110,
    };
  });

  icons.push({
    id: "folder_work",
    label: "Work",
    kind: "folder",
    target: "folder:work",
    x: 24 + 2 * 100,
    y: 24,
  });

  icons.push({
    id: "shortcut_search",
    label: "Search",
    kind: "shortcut",
    target: "/search",
    x: 24 + 2 * 100,
    y: 24 + 110,
  });

  return icons;
}

export function defaultDock(): DockItem[] {
  return DEFAULT_DOCK.map((d) => ({ ...d }));
}

export function defaultIcons(layout: DesktopLayoutId = "default"): DesktopIcon[] {
  return iconGrid(layout);
}

export const DESKTOP_LAYOUTS: Record<DesktopLayoutId, { label: string }> = {
  default: { label: "Default" },
  ops: { label: "Operations" },
  sales: { label: "Sales" },
  dev: { label: "Developer" },
};
