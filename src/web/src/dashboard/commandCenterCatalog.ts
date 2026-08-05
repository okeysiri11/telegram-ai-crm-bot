/**
 * Enterprise Command Center catalog — Sprint 32.3.2.
 * Config-driven widgets / actions / modules. No new dashboard engine.
 */

export type CommandWidgetId =
  | "mission_control"
  | "today_overview"
  | "business_kpi"
  | "quick_actions"
  | "ai_activity"
  | "business_modules"
  | "personal_scaffold"
  | "activity_feed"
  | "mission_timeline"
  | "enterprise_health"
  | "ai_recommendations";

export type QuickAction = {
  id: string;
  label: string;
  route: string;
  hint: string;
};

export type BusinessModule = {
  id: string;
  label: string;
  route: string;
  description: string;
};

export type KpiCard = {
  id: string;
  label: string;
  value: string;
  delta: string;
  tone: "up" | "flat" | "down";
  widgetKind: string;
};

/** Default visible sections — personalization can hide later.
 * EP-01: Morning Brief answers the 5 CEO questions; below — decision surfaces only.
 */
export const DEFAULT_COMMAND_LAYOUT: CommandWidgetId[] = [
  "business_kpi",
  "quick_actions",
  "mission_control",
  "enterprise_health",
];

export const QUICK_ACTIONS: QuickAction[] = [
  { id: "control_tower", label: "Decide escalations", route: "/platform-builder/control-tower", hint: "Decide" },
  { id: "mission_control", label: "Check live health", route: "/platform-builder/mission-control", hint: "Ops" },
  { id: "ai_concierge", label: "Ask Advisor to prioritize", route: "/platform-builder/concierge", hint: "AI" },
  { id: "ai_team", label: "Review running agents", route: "/platform-builder/ai-team", hint: "Team" },
  { id: "enterprise_city", label: "Glance company map", route: "/enterprise-city", hint: "Map" },
  { id: "digital_twin", label: "Inspect Twin structure", route: "/platform-builder/digital-twin", hint: "Twin" },
];

export const BUSINESS_MODULES: BusinessModule[] = [
  { id: "crm", label: "CRM", route: "/workspace/crm", description: "Клиенты и сделки" },
  { id: "analytics", label: "Analytics", route: "/platform-builder/intelligence", description: "Метрики и отчёты" },
  { id: "documents", label: "Documents", route: "/workspace/docs", description: "Документы и знания" },
  { id: "finance", label: "Finance", route: "/workspace/finance", description: "Финансы и казначейство" },
  { id: "marketing", label: "Marketing", route: "/workspace", description: "Кампании (hub)" },
  { id: "sales", label: "Sales", route: "/workspace/crm", description: "Воронка продаж" },
  { id: "production", label: "Production", route: "/workspace/drone", description: "Производство / флот" },
  { id: "ai_team", label: "AI Team", route: "/platform-builder/ai-team", description: "Команда AI" },
  { id: "knowledge", label: "Knowledge", route: "/platform-builder/knowledge", description: "База знаний" },
  { id: "settings", label: "Settings", route: "/settings", description: "Настройки" },
  { id: "enterprise_city", label: "Enterprise City", route: "/enterprise-city", description: "Визуальная навигация" },
  { id: "concierge", label: "AI Concierge", route: "/platform-builder/concierge", description: "Личный Concierge" },
];

export const KPI_CARDS: KpiCard[] = [
  { id: "sales", label: "Продажи", value: "₴ 1.28M", delta: "+8.2%", tone: "up", widgetKind: "kpi_cards" },
  { id: "clients", label: "Клиенты", value: "4 812", delta: "+124", tone: "up", widgetKind: "crm_summary" },
  { id: "deals", label: "Сделки", value: "186", delta: "+12", tone: "up", widgetKind: "crm_summary" },
  { id: "processes", label: "Активные процессы", value: "57", delta: "stable", tone: "flat", widgetKind: "workflow_queue" },
  { id: "automation", label: "AI Automation", value: "73%", delta: "+4%", tone: "up", widgetKind: "ai_assistant" },
];

export const TODAY_ITEMS = {
  tasks: [
    { id: "t1", label: "Подтвердить AI recommendation", due: "Сегодня 14:00" },
    { id: "t2", label: "Согласовать договор #884", due: "Сегодня 17:00" },
    { id: "t3", label: "Проверить воронку CRM", due: "Завтра" },
  ],
  meetings: [
    { id: "m1", label: "Standup · Operations", time: "10:00" },
    { id: "m2", label: "Клиент · Acme", time: "15:30" },
  ],
  deadlines: [
    { id: "d1", label: "Закрытие спринта пилота", due: "Пт" },
    { id: "d2", label: "Отчёт CFO", due: "Пн" },
  ],
  changes: [
    { id: "c1", label: "Workspace синхронизирован" },
    { id: "c2", label: "Concierge профиль обновлён" },
    { id: "c3", label: "Mission Control probe OK" },
  ],
};

export const AI_ACTIVITY = {
  running: ["Sales Specialist", "Ops Concierge", "Risk Monitor"],
  recent: [
    "Подготовлен brief по открытым сделкам",
    "Напомнено о дедлайне договора #884",
    "Предложен маршрут: CRM → Analytics",
  ],
  suggestions: [
    "Открыть Mission Control для проверки здоровья экосистем",
    "Запустить LiveWorkflow в выбранном Business Ecosystem",
    "Просмотреть Critical feedback в Pilot Dashboard",
  ],
  completed: ["Автоматизация follow-up · 12", "Классификация feedback · 8"],
};

// EP-01 — CEO Morning layout (localStorage reset).
const LAYOUT_KEY = "ewp_command_center_layout_v4";

export function loadCommandLayout(): CommandWidgetId[] {
  try {
    const raw = JSON.parse(localStorage.getItem(LAYOUT_KEY) || "null") as CommandWidgetId[] | null;
    if (Array.isArray(raw) && raw.length) return raw;
  } catch {
    /* ignore */
  }
  return [...DEFAULT_COMMAND_LAYOUT];
}

export function saveCommandLayout(ids: CommandWidgetId[]): CommandWidgetId[] {
  localStorage.setItem(LAYOUT_KEY, JSON.stringify(ids));
  return ids;
}

export function toggleCommandSection(id: CommandWidgetId): CommandWidgetId[] {
  const cur = loadCommandLayout();
  const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
  return saveCommandLayout(next.length ? next : [...DEFAULT_COMMAND_LAYOUT]);
}
