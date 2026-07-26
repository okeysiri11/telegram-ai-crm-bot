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
  | "personal_scaffold";

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

/** Default visible sections — personalization can hide later. */
export const DEFAULT_COMMAND_LAYOUT: CommandWidgetId[] = [
  "mission_control",
  "today_overview",
  "business_kpi",
  "quick_actions",
  "ai_activity",
  "business_modules",
  "personal_scaffold",
];

export const QUICK_ACTIONS: QuickAction[] = [
  { id: "create_client", label: "Создать клиента", route: "/workspace/crm", hint: "CRM" },
  { id: "create_task", label: "Создать задачу", route: "/workspace", hint: "Tasks" },
  { id: "create_doc", label: "Создать документ", route: "/workspace/docs", hint: "Documents" },
  { id: "open_crm", label: "Открыть CRM", route: "/workspace/crm", hint: "CRM" },
  { id: "ai_team", label: "AI Team", route: "/platform-builder/ai-team", hint: "AI" },
  { id: "analytics", label: "Analytics", route: "/platform-builder/intelligence", hint: "BI" },
  { id: "enterprise_city", label: "Enterprise City", route: "/enterprise-city", hint: "City" },
  { id: "mission_control", label: "Mission Control", route: "/platform-builder/mission-control", hint: "MC" },
];

export const BUSINESS_MODULES: BusinessModule[] = [
  { id: "crm", label: "CRM", route: "/workspace/crm", description: "Клиенты и сделки" },
  { id: "analytics", label: "Analytics", route: "/platform-builder/intelligence", description: "Метрики и отчёты" },
  { id: "documents", label: "Documents", route: "/workspace/docs", description: "Документы и знания" },
  { id: "finance", label: "Finance", route: "/workspace/finance", description: "Финансы и казначейство" },
  { id: "marketing", label: "Marketing", route: "/workspace", description: "Кампании и рост" },
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
  { id: "documents", label: "Документы", value: "942", delta: "+31", tone: "up", widgetKind: "analytics" },
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

const LAYOUT_KEY = "ewp_command_center_layout_v1";

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
