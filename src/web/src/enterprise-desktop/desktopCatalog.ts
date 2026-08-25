import type { DesktopAppDef, DesktopIcon, DesktopLayoutId, DockItem, WallpaperId } from "./types";

export const WALLPAPERS: Record<WallpaperId, { label: string; css: string }> = {
  aurora: {
    label: "Аврора",
    css: "radial-gradient(1200px 600px at 10% 0%, color-mix(in oklab, var(--eds-primary) 28%, transparent), transparent 60%), radial-gradient(900px 500px at 90% 20%, color-mix(in oklab, #3d7ea6 22%, transparent), transparent 55%), linear-gradient(160deg, #0f1419 0%, #1a2330 50%, #121820 100%)",
  },
  slate: {
    label: "Сланец",
    css: "linear-gradient(145deg, #1c222b 0%, #2a3340 45%, #171c24 100%)",
  },
  studio: {
    label: "Студия",
    css: "radial-gradient(800px 400px at 50% 0%, color-mix(in oklab, var(--eds-primary) 18%, transparent), transparent 70%), linear-gradient(180deg, #141820 0%, #0e1218 100%)",
  },
  midnight: {
    label: "Полночь",
    css: "linear-gradient(180deg, #0a0d12 0%, #121826 60%, #0b1018 100%)",
  },
  plain: {
    label: "Простой",
    css: "var(--eds-bg)",
  },
};

/** Launcher + dock application catalog. */
export const DESKTOP_APPS: DesktopAppDef[] = [
  { id: "dashboard", label: "Панель управления", path: "/dashboard", icon: "dashboard", group: "core", badgeKey: "notifications" },
  { id: "crm", label: "CRM", path: "/crm", icon: "crm", group: "core" },
  { id: "erp", label: "ERP", path: "/erp", icon: "erp", group: "core" },
  { id: "finance", label: "Финансы", path: "/analytics", icon: "analytics", group: "core" },
  { id: "knowledge", label: "База знаний", path: "/knowledge", icon: "knowledge", group: "core" },
  { id: "ai_studio", label: "Студия AI", path: "/ai-studio", icon: "ai_studio", group: "ai", badgeKey: "ai" },
  { id: "ai_agents", label: "AI-агенты", path: "/ai-agents", icon: "ai_agents", group: "ai", badgeKey: "ai" },
  { id: "marketplace", label: "Магазин решений", path: "/marketplace", icon: "marketplace", group: "ops" },
  { id: "analytics", label: "Аналитика", path: "/analytics", icon: "analytics", group: "ops" },
  { id: "settings", label: "Настройки", path: "/settings", icon: "settings", group: "tools" },
  { id: "city", label: "Корпоративный город", path: "/enterprise-city", icon: "city", group: "ops" },
  { id: "casino", label: "Casino", path: "/casino", icon: "marketplace", group: "ops" },
  { id: "production", label: "Студия производства", path: "/production-studio", icon: "projects", group: "ops", badgeKey: "jobs" },
  { id: "prod_image", label: "Студия изображений", path: "/production-studio?studio=image", icon: "projects", group: "ops" },
  { id: "prod_video", label: "Студия видео", path: "/production-studio?studio=video", icon: "projects", group: "ops" },
  { id: "prod_audio", label: "Студия аудио", path: "/production-studio?studio=audio", icon: "projects", group: "ops" },
  { id: "prod_voice", label: "Голосовая студия", path: "/production-studio?studio=voice", icon: "projects", group: "ops" },
  { id: "prod_avatar", label: "Студия аватаров", path: "/ai-studio?studio=avatar", icon: "projects", group: "ops" },
  { id: "prod_reels", label: "Фабрика Reels", path: "/production-studio?studio=reels", icon: "projects", group: "ops" },
  { id: "prod_ads", label: "Фабрика рекламы", path: "/production-studio?studio=ads", icon: "projects", group: "ops" },
  { id: "prod_creative", label: "Креативная студия", path: "/production-studio?studio=creative", icon: "projects", group: "ops" },
  { id: "prod_prompt", label: "Студия промптов", path: "/production-studio?tab=prompts", icon: "ai_studio", group: "ai" },
  { id: "prod_publish", label: "Центр публикаций", path: "/production-studio?studio=publishing", icon: "projects", group: "ops" },
  { id: "prod_runtime", label: "Исполнение производства", path: "/production-studio?tab=runtime", icon: "automation", group: "ops", badgeKey: "jobs" },
  { id: "prod_analytics", label: "Аналитика производства", path: "/production-studio?studio=analytics", icon: "analytics", group: "ops" },
  { id: "workflow_studio", label: "Студия сценариев", path: "/platform-builder/workflow-center", icon: "automation", group: "ops", badgeKey: "jobs" },
  { id: "agent_studio", label: "Студия агентов", path: "/platform-builder/builder-studio", icon: "ai_agents", group: "ai", badgeKey: "ai" },
  { id: "devtools", label: "Инструменты разработчика", path: "/command-center", icon: "integrations", group: "tools" },
  { id: "cmd_runtime", label: "Инспектор команд", path: "/command-runtime", icon: "integrations", group: "tools" },
  { id: "workflow_runtime", label: "Исполнение сценариев", path: "/workflow-runtime", icon: "automation", group: "tools" },
  { id: "automation_center", label: "Центр автоматизации", path: "/automation", icon: "automation", group: "tools" },
  { id: "business_network", label: "Бизнес-сеть", path: "/business-network", icon: "marketplace", group: "core" },
  { id: "digital_citizens", label: "Цифровые граждане", path: "/digital-citizens", icon: "hr", group: "core" },
  { id: "life_engine", label: "Движок жизни", path: "/life-engine", icon: "city", group: "ops" },
  { id: "assets", label: "Среда ресурсов", path: "/assets", icon: "erp", group: "ops" },
  { id: "spatial", label: "Пространственная среда", path: "/spatial", icon: "city", group: "ops" },
  { id: "city_visualization", label: "Визуализация города", path: "/city-visualization", icon: "city", group: "ops" },
  { id: "interactions", label: "Среда взаимодействий", path: "/interactions", icon: "city", group: "ops" },
  { id: "intelligence", label: "Среда интеллекта", path: "/intelligence", icon: "analytics", group: "ops" },
  { id: "orchestrator", label: "Оркестратор", path: "/orchestrator", icon: "integrations", group: "tools" },
  { id: "kernel", label: "Ядро предприятия", path: "/kernel", icon: "integrations", group: "tools" },
  { id: "documents", label: "Документы", path: "/documents", icon: "documents", group: "core" },
  { id: "automation", label: "Автоматизация", path: "/automation", icon: "automation", group: "ops", badgeKey: "jobs" },
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
    label: "Работа",
    kind: "folder",
    target: "folder:work",
    x: 24 + 2 * 100,
    y: 24,
  });

  icons.push({
    id: "shortcut_search",
    label: "Поиск",
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
  default: { label: "По умолчанию" },
  ops: { label: "Операции" },
  sales: { label: "Продажи" },
  dev: { label: "Разработчик" },
};
