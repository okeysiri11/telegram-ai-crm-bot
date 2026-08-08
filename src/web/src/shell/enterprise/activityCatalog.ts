/**
 * Sprint 27.1 / 41.3 — Activity Center seed (Russian-first; locale-aware helpers).
 */

export type ActivityTabId = "recent" | "notifications" | "tasks" | "ai" | "system";

export type ActivityEntry = {
  id: string;
  tab: ActivityTabId;
  title: string;
  detail: string;
  at: string;
  tone?: "ok" | "warn" | "info";
};

/** Tab label i18n keys (UI uses t()). */
export const ACTIVITY_TAB_I18N: Record<ActivityTabId, string> = {
  recent: "activity.tab.recent",
  notifications: "activity.tab.notifications",
  tasks: "activity.tab.tasks",
  ai: "activity.tab.ai",
  system: "activity.tab.system",
};

export const ACTIVITY_TABS: { id: ActivityTabId; labelKey: string }[] = [
  { id: "recent", labelKey: "activity.tab.recent" },
  { id: "notifications", labelKey: "activity.tab.notifications" },
  { id: "tasks", labelKey: "activity.tab.tasks" },
  { id: "ai", labelKey: "activity.tab.ai" },
  { id: "system", labelKey: "activity.tab.system" },
];

const ago = (m: number) => new Date(Date.now() - m * 60_000).toISOString();

/** Default Russian seed — shown when live feeds empty. */
export const SHELL_ACTIVITY_SEED: ActivityEntry[] = [
  {
    id: "r1",
    tab: "recent",
    title: "Открыта главная",
    detail: "Сессия рабочего пространства",
    at: ago(1),
    tone: "info",
  },
  {
    id: "r2",
    tab: "recent",
    title: "Синхронизация CRM",
    detail: "Активные сделки обновлены",
    at: ago(8),
    tone: "ok",
  },
  {
    id: "n1",
    tab: "notifications",
    title: "Ожидает согласования",
    detail: "2 элемента требуют внимания",
    at: ago(12),
    tone: "warn",
  },
  {
    id: "n2",
    tab: "notifications",
    title: "Приглашение принято",
    detail: "Новый участник в пространстве",
    at: ago(40),
    tone: "ok",
  },
  {
    id: "t1",
    tab: "tasks",
    title: "Фоновая задача",
    detail: "Выполняется · генерация сводки",
    at: ago(3),
    tone: "info",
  },
  {
    id: "t2",
    tab: "tasks",
    title: "Проверка состояния",
    detail: "Выполняется · мониторинг",
    at: ago(5),
    tone: "ok",
  },
  {
    id: "a1",
    tab: "ai",
    title: "AI-консьерж",
    detail: "Приоритеты на сегодня готовы",
    at: ago(6),
    tone: "info",
  },
  {
    id: "a2",
    tab: "ai",
    title: "Рекомендация AI",
    detail: "Откройте CRM → Отчёты",
    at: ago(15),
    tone: "ok",
  },
  {
    id: "s1",
    tab: "system",
    title: "Провайдеры",
    detail: "Сигнал среды в норме",
    at: ago(2),
    tone: "ok",
  },
  {
    id: "s2",
    tab: "system",
    title: "Готовность",
    detail: "Платформа готова к работе",
    at: ago(20),
    tone: "info",
  },
];
