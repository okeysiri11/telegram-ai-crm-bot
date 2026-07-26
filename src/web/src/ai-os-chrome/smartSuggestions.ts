/**
 * Path-aware smart suggestions — Sprint 32.4.
 * Uses existing routes / live snapshot hints — no new AI Engine.
 */

export type SmartSuggestion = {
  id: string;
  title: string;
  detail: string;
  route: string;
  tone: "action" | "attention" | "insight";
};

const BY_SECTION: Record<string, SmartSuggestion[]> = {
  crm: [
    { id: "crm_create", title: "Создать клиента", detail: "CRM · новый lead", route: "/workspace/crm", tone: "action" },
    { id: "crm_overdue", title: "Проверить просроченные сделки", detail: "Pipeline risk", route: "/workspace/crm", tone: "attention" },
    { id: "crm_ai", title: "AI brief по воронке", detail: "AI Team", route: "/platform-builder/ai-team", tone: "insight" },
  ],
  knowledge: [
    { id: "kb_new", title: "Найдены новые документы", detail: "Knowledge Base", route: "/platform-builder/knowledge", tone: "insight" },
    { id: "kb_docs", title: "Открыть Documents", detail: "Workspace docs", route: "/workspace/docs", tone: "action" },
  ],
  city: [
    { id: "city_prod", title: "Активен Production", detail: "Enterprise City", route: "/enterprise-city", tone: "attention" },
    { id: "city_mc", title: "Проверить Mission Control", detail: "Live ops", route: "/platform-builder/mission-control", tone: "action" },
  ],
  analytics: [
    { id: "an_kpi", title: "Изменился KPI", detail: "Intelligence", route: "/platform-builder/intelligence", tone: "attention" },
    { id: "an_dash", title: "Открыть Executive Mode", detail: "Dashboard", route: "/dashboard?mode=executive", tone: "insight" },
  ],
  dashboard: [
    { id: "dash_exec", title: "Смотреть Executive Snapshot", detail: "Что требует внимания", route: "/dashboard?mode=executive", tone: "insight" },
    { id: "dash_live", title: "Обновить Live Activity", detail: "Mission Control", route: "/platform-builder/mission-control", tone: "action" },
    { id: "dash_city", title: "Перейти в Enterprise City", detail: "Визуальная навигация", route: "/enterprise-city", tone: "action" },
  ],
  ai: [
    { id: "ai_team", title: "Проверить работающих агентов", detail: "AI Team", route: "/platform-builder/ai-team", tone: "action" },
    { id: "ai_conc", title: "Настроить Concierge", detail: "Профиль AI", route: "/platform-builder/concierge", tone: "insight" },
  ],
  finance: [
    { id: "fin_close", title: "Проверить закрытие периода", detail: "Finance", route: "/workspace/finance", tone: "attention" },
  ],
  default: [
    { id: "def_crm", title: "Открыть CRM", detail: "Клиенты и сделки", route: "/workspace/crm", tone: "action" },
    { id: "def_ai", title: "Спросить AI Concierge", detail: "Быстрые команды · ⌘⇧P", route: "/platform-builder/concierge", tone: "insight" },
    { id: "def_mc", title: "Mission Control health", detail: "Состояние платформы", route: "/platform-builder/mission-control", tone: "attention" },
    { id: "def_dash", title: "Вернуться на Dashboard", detail: "Command Center", route: "/dashboard", tone: "action" },
  ],
};

export function sectionKeyFromPath(pathname: string): string {
  if (pathname.includes("/crm") || pathname.includes("sales")) return "crm";
  if (pathname.includes("/knowledge") || pathname.includes("/docs")) return "knowledge";
  if (pathname.includes("enterprise-city") || pathname.includes("digital-twin")) return "city";
  if (pathname.includes("intelligence") || pathname.includes("analytics")) return "analytics";
  if (pathname.includes("/dashboard")) return "dashboard";
  if (pathname.includes("ai-team") || pathname.includes("/concierge") || pathname.includes("/workspace/ai"))
    return "ai";
  if (pathname.includes("finance")) return "finance";
  return "default";
}

export function suggestionsForPath(pathname: string, limit = 5): SmartSuggestion[] {
  const key = sectionKeyFromPath(pathname);
  const primary = BY_SECTION[key] || BY_SECTION.default;
  if (primary.length >= Math.min(2, limit)) return primary.slice(0, limit);
  const seen = new Set(primary.map((s) => s.id));
  const padded = [...primary];
  for (const s of BY_SECTION.default) {
    if (padded.length >= limit) break;
    if (seen.has(s.id)) continue;
    padded.push(s);
    seen.add(s.id);
  }
  return padded.slice(0, Math.max(2, Math.min(limit, padded.length)));
}
