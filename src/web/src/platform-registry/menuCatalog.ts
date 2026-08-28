/**
 * Sprint 34.2B — Web projection of Platform Registry Menu Catalog.
 * Sprint 35.1 — Offline / fallback projection only. Live SoR is
 * GET /management/v1/platform-registry/navigation (see menuApiBridge.ts).
 * Keep in sync with platform_registry/menus (Python SoR).
 */

import type { ShellIconId } from "@/shell/enterprise";
import type { ExperienceMode } from "@/ux-revolution/experienceModeStore";
import type { IntelligentNavGroup, IntelligentNavItem, NavGroupId } from "@/ux-revolution/intelligentNavGroups";

export type PlatformMenuItem = {
  id: string;
  title: string;
  titleEn?: string;
  icon: ShellIconId | string;
  route: string;
  telegramCommand?: string | null;
  requiredPermissions?: string[];
  requiredRoles?: string[];
  group: NavGroupId | "verticals";
  simple?: boolean;
  ownerOnly?: boolean;
};

/** Mirrors platform_registry MENU_CATALOG (web-visible items). */
export const PLATFORM_MENU_CATALOG: PlatformMenuItem[] = [
  { id: "ws_home", title: "Главная", titleEn: "Home", icon: "dashboard", route: "/dashboard", group: "workspace", simple: true },
  { id: "ws_desktop", title: "Рабочий стол", titleEn: "Desktop", icon: "desktop", route: "/desktop", group: "workspace", simple: true },
  { id: "ws_calendar", title: "Календарь", titleEn: "Calendar", icon: "dashboard", route: "/calendar", group: "workspace", simple: true },
  { id: "ws_tasks", title: "Задачи", titleEn: "Tasks", icon: "projects", route: "/tasks", group: "workspace", simple: true },
  { id: "ws_documents", title: "Документы", titleEn: "Documents", icon: "documents", route: "/documents", group: "workspace", simple: true },
  { id: "ws_notifications", title: "Уведомления", titleEn: "Notifications", icon: "dashboard", route: "/notifications", group: "workspace", simple: true },
  { id: "ws_settings", title: "Настройки", titleEn: "Settings", icon: "settings", route: "/settings", group: "workspace", simple: true },
  { id: "ws_search", title: "Поиск", titleEn: "Search", icon: "dashboard", route: "/search", group: "workspace", simple: true },
  { id: "biz_crm", title: "CRM", icon: "crm", route: "/crm", group: "business", simple: true },
  { id: "biz_clients", title: "Клиенты", titleEn: "Clients", icon: "crm", route: "/crm?view=clients", group: "business", simple: true },
  { id: "biz_projects", title: "Проекты", titleEn: "Projects", icon: "projects", route: "/projects", group: "business", simple: true },
  { id: "biz_finance", title: "Финансы", titleEn: "Finance", icon: "analytics", route: "/analytics", group: "business", simple: true },
  { id: "biz_erp", title: "ERP", icon: "erp", route: "/erp", group: "business" },
  { id: "biz_mfg", title: "Производство", titleEn: "Manufacturing", icon: "erp", route: "/erp?view=production", group: "business" },
  { id: "biz_marketplace", title: "Маркетплейс", titleEn: "Marketplace", icon: "marketplace", route: "/marketplace", group: "business" },
  { id: "biz_legal", title: "Юридический отдел", titleEn: "Legal", icon: "security", route: "/workspace/legal", group: "business" },
  { id: "biz_analytics", title: "Аналитика", titleEn: "Analytics", icon: "analytics", route: "/analytics", group: "business" },
  { id: "ai_agents", title: "AI-Ассистент", titleEn: "AI Assistant", icon: "ai_agents", route: "/ai-agents", group: "ai", simple: true },
  { id: "ai_studio", title: "AI Studio", icon: "ai_studio", route: "/ai-studio", group: "ai" },
  { id: "ai_production", title: "Продакшн", titleEn: "Production", icon: "ai_studio", route: "/production-studio", group: "ai" },
  { id: "ai_knowledge", title: "Знания", titleEn: "Knowledge", icon: "knowledge", route: "/knowledge", group: "ai" },
  { id: "ai_runtime", title: "AI Runtime", icon: "ai_agents", route: "/platform-builder/ai-runtime", group: "ai" },
  { id: "context_engine", title: "Context Engine", icon: "ai_agents", route: "/platform-builder/context-engine", group: "ai" },
  { id: "project_memory", title: "Project Memory", icon: "ai_agents", route: "/platform-builder/project-memory", group: "ai" },
  { id: "voice_runtime", title: "Voice Command Center", icon: "ai_agents", route: "/platform-builder/voice", group: "ai" },
  { id: "multi_agent", title: "Multi-Agent Runtime", icon: "ai_agents", route: "/platform-builder/multi-agent", group: "ai" },
  { id: "skills_sdk", title: "AI Skills & SDK", icon: "ai_agents", route: "/platform-builder/skills", group: "ai" },
  { id: "creative_factory", title: "Creative Factory", icon: "ai_agents", route: "/platform-builder/creative", group: "ai" },
  { id: "enterprise_city_runtime", title: "Enterprise City Runtime", icon: "analytics", route: "/platform", group: "platform" },
  { id: "ai_team", title: "AI Team", icon: "ai_agents", route: "/platform-builder/ai-team", group: "ai" },
  { id: "city_map", title: "Enterprise City", icon: "city", route: "/enterprise-city", group: "city" },
  { id: "city_control", title: "Control Tower", icon: "city", route: "/control-tower", group: "city" },
  { id: "plat_builder", title: "Platform Builder", icon: "builder", route: "/platform-builder", group: "platform" },
  { id: "plat_service_builder", title: "Service Builder", icon: "builder", route: "/platform-builder/service-builder", group: "platform" },
  { id: "plat_event_bus", title: "Event Bus", icon: "zap", route: "/platform-builder/event-bus", group: "platform" },
  { id: "plat_workflows", title: "Workflows", icon: "workflow", route: "/platform-builder/workflows", group: "platform" },
  { id: "plat_integrations", title: "Интеграции", titleEn: "Integrations", icon: "marketplace", route: "/platform-builder/integrations", group: "platform" },
  { id: "plat_security", title: "Безопасность", titleEn: "Security", icon: "security", route: "/identity/security", group: "platform" },
  { id: "plat_health", title: "Здоровье платформы", titleEn: "Platform Health", icon: "dashboard", route: "/health", group: "platform" },
  { id: "vert_auto", title: "Авто", titleEn: "Automotive", icon: "crm", route: "/workspace/auto", group: "business" },
  { id: "vert_crypto", title: "Crypto OTC", icon: "analytics", route: "/workspace/crypto", group: "business" },
  { id: "vert_drone", title: "Drone", icon: "projects", route: "/workspace/drone", group: "business" },
  { id: "vert_agro", title: "Агро", icon: "marketplace", route: "/workspace/agro", group: "business" },
  { id: "vert_cafe", title: "Cafe", icon: "marketplace", route: "/workspace/cafe", group: "business" },
  { id: "vert_beauty", title: "Beauty", icon: "marketplace", route: "/workspace/beauty", group: "business" },
  { id: "vert_casino", title: "Casino", titleEn: "Casino", icon: "marketplace", route: "/casino", group: "business", simple: true },
  { id: "own_dashboard", title: "Owner Dashboard", icon: "dashboard", route: "/owner", group: "owner", ownerOnly: true },
  { id: "own_god", title: "God Mode", icon: "security", route: "/platform-builder/god-mode", group: "owner", ownerOnly: true },
];

const GROUP_META: Record<string, { label: string; labelEn: string; icon: ShellIconId; simple: boolean; ownerOnly?: boolean }> = {
  workspace: { label: "Рабочее пространство", labelEn: "Workspace", icon: "desktop", simple: true },
  business: { label: "Бизнес", labelEn: "Business", icon: "crm", simple: true },
  ai: { label: "AI", labelEn: "AI", icon: "ai_agents", simple: true },
  city: { label: "Enterprise City", labelEn: "Enterprise City", icon: "city", simple: false },
  platform: { label: "Платформа", labelEn: "Platform", icon: "builder", simple: false },
  owner: { label: "Владелец", labelEn: "Owner", icon: "dashboard", simple: false, ownerOnly: true },
};

function toNavItem(m: PlatformMenuItem): IntelligentNavItem {
  return {
    id: m.id,
    label: m.title,
    route: m.route,
    icon: m.icon as ShellIconId,
    simple: Boolean(m.simple),
  };
}

/** Build intelligent nav groups from Platform Menu Catalog (34.2B). */
export function groupsFromPlatformRegistry(
  mode: ExperienceMode,
  opts?: { owner?: boolean },
): IntelligentNavGroup[] {
  const owner = opts?.owner ?? false;
  const buckets = new Map<string, PlatformMenuItem[]>();
  for (const item of PLATFORM_MENU_CATALOG) {
    if (item.ownerOnly && !owner) continue;
    const g = item.group === "verticals" ? "business" : item.group;
    if (!buckets.has(g)) buckets.set(g, []);
    buckets.get(g)!.push(item);
  }

  const order = ["workspace", "business", "ai", "city", "platform", "owner"] as const;
  const groups: IntelligentNavGroup[] = [];
  for (const gid of order) {
    const meta = GROUP_META[gid];
    const items = buckets.get(gid) || [];
    if (!meta || items.length === 0) continue;
    if (meta.ownerOnly && !owner) continue;
    if (!owner && mode === "simple" && !meta.simple) continue;
    const mapped = items
      .filter((i) => (mode === "simple" && !owner ? i.simple : true))
      .map(toNavItem);
    if (!mapped.length) continue;
    groups.push({
      id: gid as NavGroupId,
      label: meta.label,
      labelEn: meta.labelEn,
      icon: meta.icon,
      simple: meta.simple,
      ownerOnly: meta.ownerOnly,
      items: mapped,
    });
  }
  return groups;
}

export const PLATFORM_REGISTRY_SPRINT = "34.2B";
