/**
 * Sprint 42.0 — module landing content (guided workspace hubs).
 */

export type ModuleLandingDef = {
  id: string;
  route: string;
  title: string;
  purpose: string;
  description: string;
  primaryAction: { label: string; route: string };
  actions: Array<{ label: string; route: string }>;
  recent: Array<{ title: string; detail: string; route?: string }>;
  recentObjects: Array<{ title: string; detail: string; route?: string }>;
  stats: Array<{ label: string; value: string }>;
  nextStep: string;
  /** Short one-liner shown in cards */
  aiRecommendation: string;
  /** Structured AI morning brief */
  aiGuide: {
    greeting: string;
    bullets: string[];
    recommendedAction: { label: string; route: string };
  };
  estimatedMinutes: number;
  helpRoute: string;
  welcomeKey: string;
  /** When recent is empty, show empty-state CTAs */
  emptyDemoRoute: string;
  emptyTutorialRoute: string;
};

export const MODULE_LANDINGS: ModuleLandingDef[] = [
  {
    id: "crm",
    route: "/crm",
    title: "CRM",
    purpose: "Клиенты, лиды, сделки и компании в одной воронке",
    description: "Ведите продажи от первого контакта до закрытия сделки.",
    primaryAction: { label: "Создать клиента", route: "/crm?view=clients&action=create" },
    actions: [
      { label: "Клиенты", route: "/crm?view=clients" },
      { label: "Лиды", route: "/crm?view=leads" },
      { label: "Сделки", route: "/crm?view=deals" },
      { label: "Компании", route: "/crm?view=companies" },
    ],
    recentObjects: [
      { title: "Acme Travel", detail: "Клиент · активен", route: "/crm?view=clients" },
      { title: "Корпоративные билеты", detail: "Лид · новый", route: "/crm?view=leads" },
    ],
    recent: [
      { title: "Новый лид", detail: "Корпоративные билеты", route: "/crm?view=leads" },
      { title: "Сделка обновлена", detail: "Подписка B2B API", route: "/crm?view=deals" },
    ],
    stats: [
      { label: "Лиды", value: "5" },
      { label: "Сделки", value: "12" },
      { label: "Просрочено", value: "2" },
    ],
    nextStep: "Создайте клиента или откройте воронку сделок",
    aiRecommendation: "Квалифицируйте лиды со статусом «новый»",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["5 новых лидов", "2 просроченные задачи", "1 договор ожидает согласования"],
      recommendedAction: { label: "Открыть CRM", route: "/crm?view=leads" },
    },
    estimatedMinutes: 15,
    helpRoute: "/knowledge?q=crm",
    welcomeKey: "welcome.crm",
    emptyDemoRoute: "/crm?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=crm",
  },
  {
    id: "crypto",
    route: "/workspace/crypto",
    title: "Crypto OTC",
    purpose: "Курсы, сделки, кошельки и переводы",
    description: "Сопровождайте OTC-сделки и расчёты в одном месте.",
    primaryAction: { label: "Создать OTC-сделку", route: "/workspace/crypto?action=deal" },
    actions: [
      { label: "Курсы сегодня", route: "/workspace/crypto?view=rates" },
      { label: "Сделки", route: "/workspace/crypto?view=deals" },
      { label: "Кошельки", route: "/workspace/crypto?view=wallets" },
      { label: "Переводы", route: "/workspace/crypto?view=transfers" },
    ],
    recentObjects: [{ title: "USDT/UAH", detail: "Ожидает подтверждения", route: "/workspace/crypto?view=deals" }],
    recent: [{ title: "OTC", detail: "Ожидает подтверждения" }],
    stats: [
      { label: "Сделки", value: "3" },
      { label: "Ожидание", value: "1" },
      { label: "Кошельки", value: "4" },
    ],
    nextStep: "Создайте OTC-сделку или проверьте курсы",
    aiRecommendation: "Проверьте сделки со статусом «ожидание»",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["1 сделка ожидает подтверждения", "Курсы обновлены 5 мин назад", "2 перевода в обработке"],
      recommendedAction: { label: "Создать OTC-сделку", route: "/workspace/crypto?action=deal" },
    },
    estimatedMinutes: 15,
    helpRoute: "/knowledge?q=crypto",
    welcomeKey: "welcome.crypto",
    emptyDemoRoute: "/workspace/crypto?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=crypto",
  },
  {
    id: "drone",
    route: "/workspace/drone",
    title: "БПЛА",
    purpose: "Флот, миссии, производство и обслуживание БПЛА",
    description: "Управляйте UAV-проектами, миссиями и складом.",
    primaryAction: { label: "Создать дрон", route: "/workspace/drone?action=create" },
    actions: [
      { label: "Флот", route: "/workspace/drone?view=fleet" },
      { label: "Миссии", route: "/workspace/drone?view=missions" },
      { label: "Производство", route: "/workspace/drone?view=mfg" },
      { label: "Склад", route: "/workspace/drone?view=warehouse" },
      { label: "Обслуживание", route: "/workspace/drone?view=maintenance" },
    ],
    recentObjects: [{ title: "UAV-04", detail: "Готов · батарея 92%", route: "/workspace/drone?view=fleet" }],
    recent: [{ title: "Миссия", detail: "Облёт участка A", route: "/workspace/drone?view=missions" }],
    stats: [
      { label: "Флот", value: "8" },
      { label: "Миссии", value: "2" },
      { label: "ТО", value: "1" },
    ],
    nextStep: "Создайте дрон или продолжите миссию",
    aiRecommendation: "Продолжить предыдущую миссию",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["2 активные миссии", "1 аппарат на обслуживании", "Склад: 4 комплекта готовы"],
      recommendedAction: { label: "Создать дрон", route: "/workspace/drone?action=create" },
    },
    estimatedMinutes: 20,
    helpRoute: "/knowledge?q=drone",
    welcomeKey: "welcome.drone",
    emptyDemoRoute: "/workspace/drone?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=drone",
  },
  {
    id: "auto",
    route: "/workspace/auto",
    title: "Авто",
    purpose: "Автомобили, клиенты, продажи и склад",
    description: "Дилерские операции и каталог в одном пространстве.",
    primaryAction: { label: "Добавить автомобиль", route: "/workspace/auto?action=vehicle" },
    actions: [
      { label: "Автомобили", route: "/workspace/auto?view=cars" },
      { label: "Клиенты", route: "/workspace/auto?view=clients" },
      { label: "Продажи", route: "/workspace/auto?view=sales" },
      { label: "Импорт", route: "/workspace/auto?view=import" },
      { label: "Склад", route: "/workspace/auto?view=warehouse" },
    ],
    recentObjects: [{ title: "SUV · Toyota", detail: "В продаже", route: "/workspace/auto?view=cars" }],
    recent: [{ title: "Листинг", detail: "SUV · обновлён" }],
    stats: [
      { label: "Авто", value: "24" },
      { label: "Лиды", value: "6" },
      { label: "Сделки", value: "3" },
    ],
    nextStep: "Добавьте автомобиль в каталог",
    aiRecommendation: "добавить фотографии автомобилей",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["Новые заявки", "Сделки", "Автомобили без фото"],
      recommendedAction: { label: "Исправить", route: "/workspace/auto?view=cars&action=photos" },
    },
    estimatedMinutes: 15,
    helpRoute: "/knowledge?q=auto",
    welcomeKey: "welcome.auto",
    emptyDemoRoute: "/workspace/auto?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=auto",
  },
  {
    id: "agro",
    route: "/workspace/agro",
    title: "Агро",
    purpose: "Поля, техника, сенсоры и урожай",
    description: "Планируйте сезоны и следите за участками.",
    primaryAction: { label: "Открыть ферму", route: "/workspace/agro?view=fields" },
    actions: [
      { label: "Поля", route: "/workspace/agro?view=fields" },
      { label: "Техника", route: "/workspace/agro?view=equipment" },
      { label: "Сенсоры", route: "/workspace/agro?view=sensors" },
      { label: "Урожай", route: "/workspace/agro?view=harvest" },
    ],
    recentObjects: [{ title: "Участок Север", detail: "Влажность в норме", route: "/workspace/agro?view=fields" }],
    recent: [{ title: "Поле", detail: "Участок Север" }],
    stats: [
      { label: "Поля", value: "7" },
      { label: "Сенсоры", value: "18" },
      { label: "Техника", value: "5" },
    ],
    nextStep: "Откройте карту полей",
    aiRecommendation: "Обновите статус сезонных работ",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["2 поля требуют полива", "1 сенсор офлайн", "Урожайная неделя через 12 дней"],
      recommendedAction: { label: "Открыть ферму", route: "/workspace/agro?view=fields" },
    },
    estimatedMinutes: 15,
    helpRoute: "/knowledge?q=agro",
    welcomeKey: "welcome.agro",
    emptyDemoRoute: "/workspace/agro?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=agro",
  },
  {
    id: "marketplace",
    route: "/marketplace",
    title: "Маркетплейс",
    purpose: "Товары, заказы, платежи и поставщики",
    description: "Публикуйте и продавайте на корпоративном marketplace.",
    primaryAction: { label: "Создать продукт", route: "/marketplace?action=create" },
    actions: [
      { label: "Продукты", route: "/marketplace?view=products" },
      { label: "Заказы", route: "/marketplace?view=orders" },
      { label: "Платежи", route: "/marketplace?view=payments" },
      { label: "Поставщики", route: "/marketplace?view=vendors" },
    ],
    recentObjects: [{ title: "API Pack", detail: "Опубликован", route: "/marketplace?view=products" }],
    recent: [{ title: "Заказ", detail: "Ожидает оплаты" }],
    stats: [
      { label: "Продукты", value: "14" },
      { label: "Заказы", value: "5" },
      { label: "Платежи", value: "3" },
    ],
    nextStep: "Создайте продукт или откройте заказы",
    aiRecommendation: "Проверьте популярные предложения недели",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["5 новых заказов", "2 платежа ожидают", "1 продукт без описания"],
      recommendedAction: { label: "Создать продукт", route: "/marketplace?action=create" },
    },
    estimatedMinutes: 10,
    helpRoute: "/knowledge?q=marketplace",
    welcomeKey: "welcome.marketplace",
    emptyDemoRoute: "/marketplace?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=marketplace",
  },
  {
    id: "analytics",
    route: "/analytics",
    title: "Аналитика",
    purpose: "Дашборды, отчёты, прогнозы и KPI",
    description: "Смотрите показатели и делитесь отчётами с командой.",
    primaryAction: { label: "Открыть дашборд", route: "/analytics?view=dashboard" },
    actions: [
      { label: "Дашборды", route: "/analytics?view=dashboard" },
      { label: "Отчёты", route: "/analytics?view=reports" },
      { label: "Прогнозы", route: "/analytics?view=forecasts" },
      { label: "KPI", route: "/analytics?view=kpi" },
    ],
    recentObjects: [{ title: "Выручка месяца", detail: "Обновлён сегодня", route: "/analytics?view=reports" }],
    recent: [{ title: "Отчёт", detail: "Выручка месяца" }],
    stats: [
      { label: "KPI", value: "8" },
      { label: "Отчёты", value: "4" },
      { label: "Алерты", value: "1" },
    ],
    nextStep: "Откройте дашборд и выберите период",
    aiRecommendation: "Сравните конверсию лидов за 30 дней",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["Конверсия лидов +4% за неделю", "1 KPI ниже цели", "Прогноз выручки готов"],
      recommendedAction: { label: "Открыть дашборд", route: "/analytics?view=dashboard" },
    },
    estimatedMinutes: 10,
    helpRoute: "/knowledge?q=analytics",
    welcomeKey: "welcome.analytics",
    emptyDemoRoute: "/analytics?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=analytics",
  },
  {
    id: "legal",
    route: "/workspace/legal",
    title: "Юридический",
    purpose: "Дела, договоры, документы и сроки",
    description: "Контролируйте согласования и дедлайны.",
    primaryAction: { label: "Создать договор", route: "/workspace/legal?action=contract" },
    actions: [
      { label: "Дела", route: "/workspace/legal?view=cases" },
      { label: "Договоры", route: "/workspace/legal?view=contracts" },
      { label: "Документы", route: "/workspace/legal?view=documents" },
      { label: "Сроки", route: "/workspace/legal?view=deadlines" },
    ],
    recentObjects: [{ title: "Договор B2B", detail: "Ожидает подписи", route: "/workspace/legal?view=contracts" }],
    recent: [{ title: "Договор", detail: "Ожидает подписи" }],
    stats: [
      { label: "Договоры", value: "9" },
      { label: "Сроки", value: "3" },
      { label: "Согласования", value: "2" },
    ],
    nextStep: "Создайте договор или откройте сроки",
    aiRecommendation: "Есть документы со сроком на этой неделе",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["1 договор ожидает согласования", "3 срока на этой неделе", "2 шаблона обновлены"],
      recommendedAction: { label: "Создать договор", route: "/workspace/legal?action=contract" },
    },
    estimatedMinutes: 15,
    helpRoute: "/knowledge?q=legal",
    welcomeKey: "welcome.legal",
    emptyDemoRoute: "/workspace/legal?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=legal",
  },
  {
    id: "knowledge",
    route: "/knowledge",
    title: "Знания",
    purpose: "Статьи, документы и AI-знания",
    description: "Инструкции и ответы для команды в одном месте.",
    primaryAction: { label: "Открыть знания", route: "/knowledge?view=articles" },
    actions: [
      { label: "Статьи", route: "/knowledge?view=articles" },
      { label: "Документы", route: "/knowledge?view=documents" },
      { label: "AI-знания", route: "/knowledge?view=ai" },
      { label: "Поиск", route: "/knowledge?view=search" },
    ],
    recentObjects: [{ title: "Как создать лид", detail: "Статья", route: "/knowledge?view=articles" }],
    recent: [{ title: "Карточка", detail: "Как создать лид" }],
    stats: [
      { label: "Статьи", value: "42" },
      { label: "Документы", value: "18" },
      { label: "Устаревшие", value: "3" },
    ],
    nextStep: "Откройте базу знаний или найдите инструкцию",
    aiRecommendation: "Обновите устаревшие карточки",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["3 карточки устарели", "Новый гайд по CRM готов", "База знаний проиндексирована"],
      recommendedAction: { label: "Открыть знания", route: "/knowledge?view=articles" },
    },
    estimatedMinutes: 8,
    helpRoute: "/knowledge?view=guide",
    welcomeKey: "welcome.knowledge",
    emptyDemoRoute: "/knowledge?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide",
  },
  {
    id: "cafe",
    route: "/workspace/cafe",
    title: "Кафе",
    purpose: "Заказы, меню и смены",
    description: "Операции заведения в одном рабочем месте.",
    primaryAction: { label: "Открыть заказы", route: "/workspace/cafe?view=orders" },
    actions: [
      { label: "Заказы", route: "/workspace/cafe?view=orders" },
      { label: "Меню", route: "/workspace/cafe?view=menu" },
      { label: "Смены", route: "/workspace/cafe?view=shifts" },
    ],
    recentObjects: [{ title: "Заказ #128", detail: "Готовится", route: "/workspace/cafe?view=orders" }],
    recent: [{ title: "Заказ", detail: "Готовится" }],
    stats: [
      { label: "Открытые", value: "4" },
      { label: "Смена", value: "1" },
    ],
    nextStep: "Просмотрите открытые заказы",
    aiRecommendation: "Проверьте загрузку смены",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["4 открытых заказа", "Смена укомплектована", "2 позиции меню без фото"],
      recommendedAction: { label: "Открыть заказы", route: "/workspace/cafe?view=orders" },
    },
    estimatedMinutes: 10,
    helpRoute: "/knowledge?q=cafe",
    welcomeKey: "welcome.cafe",
    emptyDemoRoute: "/workspace/cafe?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=cafe",
  },
  {
    id: "ai",
    route: "/ai-agents",
    title: "AI",
    purpose: "AI-ассистент и агенты",
    description: "Задавайте вопросы и получайте рекомендации.",
    primaryAction: { label: "Открыть ассистента", route: "/ai-agents?view=assistant" },
    actions: [
      { label: "Ассистент", route: "/ai-agents?view=assistant" },
      { label: "Знания", route: "/knowledge?view=articles" },
    ],
    recentObjects: [{ title: "Утренняя сводка", detail: "Готова", route: "/ai-agents?view=assistant" }],
    recent: [{ title: "Сводка", detail: "Утренние приоритеты" }],
    stats: [
      { label: "Сообщения", value: "12" },
      { label: "Задачи", value: "3" },
    ],
    nextStep: "Задайте вопрос ассистенту",
    aiRecommendation: "Суммируйте открытые сделки CRM",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["Сводка готова", "3 задачи от AI", "Рекомендация: открыть CRM"],
      recommendedAction: { label: "Открыть CRM", route: "/crm" },
    },
    estimatedMinutes: 5,
    helpRoute: "/knowledge?q=ai",
    welcomeKey: "welcome.ai",
    emptyDemoRoute: "/ai-agents?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=ai",
  },
  {
    id: "platform",
    route: "/platform-builder",
    title: "Платформа",
    purpose: "Конструкторы и инфраструктура",
    description: "Builder Studio, runtime и управление платформой.",
    primaryAction: { label: "Центр управления", route: "/platform-builder/ops-center" },
    actions: [
      { label: "Центр управления", route: "/platform-builder/ops-center" },
      { label: "Builder", route: "/platform-builder/builder-studio" },
      { label: "Runtime", route: "/platform-builder/runtime" },
    ],
    recentObjects: [{ title: "Центр управления", detail: "Ops strips", route: "/platform-builder/ops-center" }],
    recent: [{ title: "Ops", detail: "Инженерные панели" }],
    stats: [
      { label: "Сборки", value: "2" },
      { label: "Runtime", value: "ok" },
    ],
    nextStep: "Откройте Центр управления платформой",
    aiRecommendation: "Соберите инженерные панели в одном месте",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["Runtime в норме", "1 черновик workflow", "2 предупреждения governance"],
      recommendedAction: { label: "Центр управления", route: "/platform-builder/ops-center" },
    },
    estimatedMinutes: 20,
    helpRoute: "/knowledge?q=platform",
    welcomeKey: "welcome.platform",
    emptyDemoRoute: "/platform-builder?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=platform",
  },
  {
    id: "owner",
    route: "/owner",
    title: "Владелец",
    purpose: "Панель владельца платформы",
    description: "Здоровье, аудит и стратегический обзор.",
    primaryAction: { label: "Открыть панель", route: "/owner?view=overview" },
    actions: [
      { label: "Состояние", route: "/health" },
      { label: "Безопасность", route: "/identity/security" },
    ],
    recentObjects: [{ title: "Аудит", detail: "Отчёт готов", route: "/owner" }],
    recent: [{ title: "Аудит", detail: "Отчёт готов" }],
    stats: [
      { label: "Эскалации", value: "2" },
      { label: "Здоровье", value: "ok" },
    ],
    nextStep: "Проверьте состояние платформы",
    aiRecommendation: "Есть 2 эскалации в центре управления",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["2 эскалации", "Аудит готов", "Сеть в норме"],
      recommendedAction: { label: "Открыть панель", route: "/owner" },
    },
    estimatedMinutes: 10,
    helpRoute: "/knowledge?q=owner",
    welcomeKey: "welcome.owner",
    emptyDemoRoute: "/owner?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=owner",
  },
  {
    id: "documents",
    route: "/documents",
    title: "Документы",
    purpose: "Файлы компании",
    description: "Загрузка и обмен документами рядом со сделками.",
    primaryAction: { label: "Загрузить файл", route: "/documents?action=upload" },
    actions: [
      { label: "Все файлы", route: "/documents" },
      { label: "Недавние", route: "/documents?view=recent" },
    ],
    recentObjects: [{ title: "Договор.pdf", detail: "Загружен", route: "/documents" }],
    recent: [{ title: "Договор", detail: "PDF · загружен" }],
    stats: [
      { label: "Файлы", value: "36" },
      { label: "Сегодня", value: "2" },
    ],
    nextStep: "Загрузите договор или откройте недавние файлы",
    aiRecommendation: "Привяжите документ к активной сделке",
    aiGuide: {
      greeting: "Доброе утро.",
      bullets: ["2 файла загружены сегодня", "1 договор без привязки к сделке"],
      recommendedAction: { label: "Загрузить файл", route: "/documents?action=upload" },
    },
    estimatedMinutes: 5,
    helpRoute: "/knowledge?q=documents",
    welcomeKey: "welcome.documents",
    emptyDemoRoute: "/documents?demo=1",
    emptyTutorialRoute: "/knowledge?view=guide&topic=documents",
  },
];

export function landingForPath(pathname: string): ModuleLandingDef | undefined {
  const base = (pathname.split("?")[0] || pathname).replace(/\/$/, "") || "/";
  const exact = MODULE_LANDINGS.find((m) => m.route === base);
  if (exact) return exact;
  return MODULE_LANDINGS.find(
    (m) => base === m.route || base.startsWith(`${m.route}/`) || base.startsWith(m.route),
  );
}
