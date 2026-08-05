/**
 * Sprint 30.3 — Beta home catalog (Russian demo data for first visual interface).
 */

export type BetaHomeLink = { id: string; title: string; subtitle: string; route: string };

export const BETA_RECENT_PROJECTS: BetaHomeLink[] = [
  { id: "p1", title: "Запуск CRM", subtitle: "Активный · 72%", route: "/projects" },
  { id: "p2", title: "Онбординг дилеров", subtitle: "В работе", route: "/projects" },
  { id: "p3", title: "Город предприятия", subtitle: "Превью", route: "/enterprise-city" },
];

export const BETA_RECENT_DOCUMENTS: BetaHomeLink[] = [
  { id: "d1", title: "Политика безопасности", subtitle: "Документы", route: "/documents" },
  { id: "d2", title: "Бриф владельца", subtitle: "Знания", route: "/knowledge" },
  { id: "d3", title: "Договор с клиентом", subtitle: "Шаблоны", route: "/documents" },
];

export const BETA_AI_AGENTS: BetaHomeLink[] = [
  { id: "a1", title: "Ops Copilot", subtitle: "Операции", route: "/ai-agents" },
  { id: "a2", title: "AI-консьерж", subtitle: "Помощник", route: "/platform-builder/concierge" },
  { id: "a3", title: "Команда продаж", subtitle: "CRM", route: "/platform-builder/ai-team" },
];

export const BETA_RECENT_EVENTS: BetaHomeLink[] = [
  { id: "e1", title: "Вход через Google", subtitle: "Безопасность", route: "/identity/security" },
  { id: "e2", title: "Создан проект", subtitle: "Проекты", route: "/projects" },
  { id: "e3", title: "Обновлён граф знаний", subtitle: "Знания", route: "/knowledge" },
];

export const CLIENT_DASHBOARD_SECTIONS = [
  { id: "requests", title: "Мои заявки", route: "/crm?view=requests", hint: "Статус обращений" },
  { id: "projects", title: "Мои проекты", route: "/projects", hint: "Активные проекты" },
  { id: "documents", title: "Мои документы", route: "/documents", hint: "Договоры и файлы" },
  { id: "messages", title: "Мои сообщения", route: "/platform-builder/concierge", hint: "Переписка с командой" },
  { id: "history", title: "История", route: "/identity/activity", hint: "Недавние действия" },
] as const;

export const DEALER_DASHBOARD_SECTIONS = [
  { id: "clients", title: "Клиенты", route: "/crm?view=clients", hint: "База дилера" },
  { id: "orders", title: "Заказы", route: "/erp", hint: "Заявки и поставки" },
  { id: "stats", title: "Статистика", route: "/analytics", hint: "KPI дилера" },
  { id: "sales", title: "Продажи", route: "/workspace/crm", hint: "Воронка продаж" },
  { id: "crm", title: "CRM", route: "/crm", hint: "Рабочее пространство CRM" },
] as const;

export const OWNER_BETA_METRICS = [
  { id: "health", title: "Состояние платформы", value: "ok", route: "/health" },
  { id: "status", title: "Статус предприятия", value: "beta", route: "/dashboard" },
  { id: "ai", title: "Среда AI", value: "онлайн", route: "/ai-agents" },
  { id: "security", title: "Безопасность", value: "ок", route: "/identity/security" },
  { id: "arch", title: "Архитектура", value: "ядро", route: "/kernel" },
  { id: "kg", title: "Граф знаний", value: "активен", route: "/platform-builder/knowledge" },
  { id: "city", title: "Среда города", value: "live", route: "/city" },
  { id: "metrics", title: "Системные метрики", value: "пульс", route: "/platform-builder/mission-control" },
] as const;

/** Production studios highlighted on Beta home + coming-soon flags */
export const BETA_PRODUCTION_STUDIOS = [
  { id: "video", label: "Видео", available: true },
  { id: "image", label: "Изображения", available: true },
  { id: "presentation", label: "Презентации", available: true },
  { id: "voice", label: "Голос", available: true },
  { id: "prompt", label: "Библиотека промптов", available: true },
  { id: "reels", label: "Reels", available: true },
  { id: "brand", label: "Бренд-ассеты", available: true },
] as const;

export const COMING_SOON_RU = "Скоро будет доступно";
