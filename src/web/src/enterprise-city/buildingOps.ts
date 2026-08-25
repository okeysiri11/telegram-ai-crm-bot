/**
 * Sprint 30.4 — Building operational metadata for City inspector / cards.
 */

import type { CityBuildingId } from "./cityCatalog";

export type BuildingHealth = "online" | "warning" | "critical" | "maintenance";

export type BuildingQuickAction = {
  id: string;
  label: string;
  route: string;
};

export type BuildingOpsMeta = {
  owner: string;
  activeUsers: number;
  health: BuildingHealth;
  description: string;
  quickActions: BuildingQuickAction[];
};

const DEFAULT_OPS: BuildingOpsMeta = {
  owner: "Платформа",
  activeUsers: 3,
  health: "online",
  description: "Модуль предприятия ADOS",
  quickActions: [{ id: "open", label: "Открыть модуль", route: "/dashboard" }],
};

const OPS: Partial<Record<CityBuildingId, BuildingOpsMeta>> = {
  plaza: {
    owner: "City Runtime",
    activeUsers: 24,
    health: "online",
    description: "Центральная площадь — точка навигации по городу",
    quickActions: [
      { id: "home", label: "На главную", route: "/dashboard" },
      { id: "owner", label: "Панель владельца", route: "/owner" },
    ],
  },
  crm: {
    owner: "Директор по продажам",
    activeUsers: 12,
    health: "warning",
    description: "Клиенты, сделки и воронка продаж",
    quickActions: [
      { id: "open", label: "Открыть CRM", route: "/crm" },
      { id: "create", label: "Создать клиента", route: "/crm?action=create_client" },
    ],
  },
  erp: {
    owner: "Операционный директор",
    activeUsers: 8,
    health: "online",
    description: "Операции, склад и ресурсы предприятия",
    quickActions: [{ id: "open", label: "Открыть ERP", route: "/erp" }],
  },
  warehouse: {
    owner: "Начальник склада",
    activeUsers: 5,
    health: "online",
    description: "Складские остатки и поставки",
    quickActions: [{ id: "open", label: "Склад ERP", route: "/erp?view=warehouse" }],
  },
  legal: {
    owner: "Юридический отдел",
    activeUsers: 4,
    health: "online",
    description: "Договоры, риски и юридические процессы",
    quickActions: [{ id: "open", label: "Юридический модуль", route: "/workspace/legal" }],
  },
  casino: {
    owner: "Casino vertical",
    activeUsers: 6,
    health: "online",
    description: "Play-money casino — Odessa Prime venue, roulette demo",
    quickActions: [
      { id: "open", label: "Open casino", route: "/casino" },
      { id: "venue", label: "Odessa Prime", route: "/casino/venues/odessa-prime" },
    ],
  },
  marketing: {
    owner: "Маркетинг",
    activeUsers: 6,
    health: "online",
    description: "Кампании и рост",
    quickActions: [{ id: "open", label: "Маркетинг", route: "/marketplace" }],
  },
  finance: {
    owner: "Финансовый директор",
    activeUsers: 7,
    health: "warning",
    description: "Финансы и отчётность",
    quickActions: [{ id: "open", label: "Финансы", route: "/workspace/finance" }],
  },
  security: {
    owner: "Служба безопасности",
    activeUsers: 3,
    health: "online",
    description: "Безопасность, сессии и аудит",
    quickActions: [
      { id: "open", label: "Безопасность", route: "/security" },
      { id: "isam", label: "Центр безопасности", route: "/identity/security" },
    ],
  },
  ai_team: {
    owner: "AI Runtime",
    activeUsers: 15,
    health: "online",
    description: "Центр AI-агентов и команд",
    quickActions: [{ id: "open", label: "AI-Агенты", route: "/ai-agents" }],
  },
  production: {
    owner: "Production Studio",
    activeUsers: 9,
    health: "online",
    description: "Студия продакшна — видео, изображения, голос",
    quickActions: [{ id: "open", label: "Продакшн", route: "/production-studio" }],
  },
  knowledge: {
    owner: "Knowledge Graph",
    activeUsers: 6,
    health: "online",
    description: "База знаний предприятия",
    quickActions: [{ id: "open", label: "Знания", route: "/knowledge" }],
  },
  documents: {
    owner: "Документооборот",
    activeUsers: 11,
    health: "online",
    description: "Документы и файлы",
    quickActions: [{ id: "open", label: "Документы", route: "/documents" }],
  },
  developer: {
    owner: "Платформенная команда",
    activeUsers: 4,
    health: "online",
    description: "Инструменты разработчика и командный центр",
    quickActions: [{ id: "open", label: "Разработчик", route: "/command-center" }],
  },
  analytics: {
    owner: "Аналитика",
    activeUsers: 5,
    health: "online",
    description: "Аналитика и KPI",
    quickActions: [{ id: "open", label: "Аналитика", route: "/analytics" }],
  },
  marketplace: {
    owner: "Marketplace",
    activeUsers: 4,
    health: "online",
    description: "Магазин решений",
    quickActions: [{ id: "open", label: "Маркетплейс", route: "/marketplace" }],
  },
  admin: {
    owner: "Администрация",
    activeUsers: 2,
    health: "online",
    description: "Администрирование платформы",
    quickActions: [{ id: "open", label: "Администрирование", route: "/settings" }],
  },
  dashboard: {
    owner: "Владелец",
    activeUsers: 18,
    health: "online",
    description: "Главная панель предприятия",
    quickActions: [{ id: "open", label: "Главная", route: "/dashboard" }],
  },
};

export function buildingOps(id: CityBuildingId, routeFallback = "/dashboard"): BuildingOpsMeta {
  const hit = OPS[id];
  if (hit) return hit;
  return {
    ...DEFAULT_OPS,
    quickActions: [{ id: "open", label: "Открыть модуль", route: routeFallback }],
  };
}

export function healthFromLiveTone(
  tone: string,
  notifications: number,
  tasks: number,
): BuildingHealth {
  if (tone === "alert") return "critical";
  if (notifications >= 4 || tasks >= 6) return "warning";
  if (tone === "idle" && tasks === 0 && notifications === 0) return "maintenance";
  return "online";
}

export const HEALTH_LABEL_RU: Record<BuildingHealth, string> = {
  online: "Онлайн",
  warning: "Предупреждение",
  critical: "Критично",
  maintenance: "Обслуживание",
};
