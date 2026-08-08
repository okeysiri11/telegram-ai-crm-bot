/**
 * Sprint 41.2 — expanded module help (related modules + coverage).
 */

export type ModuleHelp = {
  moduleId: string;
  route: string;
  purpose: string;
  why: string;
  expectedResult: string;
  workflow: string;
  difficulty: "лёгкий" | "средний" | "сложный";
  setupMinutes: number;
  example: string;
  related: string[];
};

export const MODULE_HELP_CATALOG: ModuleHelp[] = [
  {
    moduleId: "dashboard",
    route: "/dashboard",
    purpose: "Сводка по работе компании за сегодня",
    why: "Быстро понять, что требует внимания",
    expectedResult: "KPI и быстрые ссылки на рабочие модули",
    workflow: "Главная → выберите модуль из карточек",
    difficulty: "лёгкий",
    setupMinutes: 2,
    example: "GlobeFly: открытые лиды и активные сделки",
    related: ["crm", "tasks", "analytics"],
  },
  {
    moduleId: "crm",
    route: "/crm",
    purpose: "Лиды, клиенты и сделки в одной воронке",
    why: "Когда нужно вести продажи без Excel",
    expectedResult: "Лид → клиент → сделка",
    workflow: "CRM → создать лид → квалифицировать → сделка",
    difficulty: "средний",
    setupMinutes: 15,
    example: "Лид «Корпоративные билеты Q3»",
    related: ["tasks", "documents", "analytics"],
  },
  {
    moduleId: "documents",
    route: "/documents",
    purpose: "Файлы и документы компании",
    why: "Когда договор или прайс нужны рядом со сделкой",
    expectedResult: "Файл загружен и доступен команде",
    workflow: "Документы → Загрузить → Открыть / Скачать",
    difficulty: "лёгкий",
    setupMinutes: 5,
    example: "Договор PDF для клиента",
    related: ["crm", "ai"],
  },
  {
    moduleId: "ai",
    route: "/ai-agents",
    purpose: "AI-ассистент для вопросов и рекомендаций",
    why: "Когда нужна сводка или черновик ответа",
    expectedResult: "Ответ и рекомендации на языке интерфейса",
    workflow: "Ассистент → вопрос → сводка",
    difficulty: "лёгкий",
    setupMinutes: 3,
    example: "«Суммируй открытые сделки»",
    related: ["crm", "analytics", "knowledge"],
  },
  {
    moduleId: "analytics",
    route: "/analytics",
    purpose: "Отчёты и графики",
    why: "Когда нужно оценить результат продаж",
    expectedResult: "Дашборд с фильтрами",
    workflow: "Отчёты → период → графики",
    difficulty: "средний",
    setupMinutes: 10,
    example: "Выручка за месяц",
    related: ["crm", "dashboard"],
  },
  {
    moduleId: "tasks",
    route: "/tasks",
    purpose: "Задачи и назначения",
    why: "Когда нужен follow-up по лиду или сделке",
    expectedResult: "Задача назначена и закрыта",
    workflow: "Задачи → Создать → Назначить → Завершить",
    difficulty: "лёгкий",
    setupMinutes: 5,
    example: "«Перезвонить клиенту»",
    related: ["crm", "calendar"],
  },
  {
    moduleId: "calendar",
    route: "/calendar",
    purpose: "Календарь встреч и дедлайнов",
    why: "Когда планируете звонки и встречи",
    expectedResult: "Событие видно в календаре",
    workflow: "Календарь → создать событие",
    difficulty: "лёгкий",
    setupMinutes: 5,
    example: "Встреча с клиентом в 15:00",
    related: ["tasks", "crm"],
  },
  {
    moduleId: "settings",
    route: "/settings",
    purpose: "Настройки профиля и интерфейса",
    why: "Язык, плотность, масштаб, режим интерфейса",
    expectedResult: "Предпочтения сохранены",
    workflow: "Настройки → Интерфейс → изменить",
    difficulty: "лёгкий",
    setupMinutes: 3,
    example: "Масштаб 110%, плотность Compact",
    related: ["dashboard", "profile"],
  },
  {
    moduleId: "profile",
    route: "/identity/profile",
    purpose: "Профиль пользователя",
    why: "Когда нужно обновить имя или контакты",
    expectedResult: "Данные профиля сохранены",
    workflow: "Профиль → изменить → сохранить",
    difficulty: "лёгкий",
    setupMinutes: 2,
    example: "Сменить отображаемое имя",
    related: ["settings"],
  },
  {
    moduleId: "notifications",
    route: "/notifications",
    purpose: "Центр уведомлений",
    why: "Когда нужно просмотреть непрочитанные события",
    expectedResult: "Список уведомлений и статус прочтения",
    workflow: "Уведомления → открыть → отметить",
    difficulty: "лёгкий",
    setupMinutes: 1,
    example: "Новый лид в CRM",
    related: ["dashboard", "crm"],
  },
  {
    moduleId: "knowledge",
    route: "/knowledge",
    purpose: "База знаний",
    why: "Когда ищете инструкции и ответы",
    expectedResult: "Найдена релевантная карточка",
    workflow: "Знания → поиск → открыть",
    difficulty: "лёгкий",
    setupMinutes: 5,
    example: "Как создать лид",
    related: ["ai", "documents"],
  },
  {
    moduleId: "projects",
    route: "/projects",
    purpose: "Проекты и статусы работ",
    why: "Когда ведёте инициативы помимо сделок",
    expectedResult: "Проект создан и отслеживается",
    workflow: "Проекты → создать → статусы",
    difficulty: "средний",
    setupMinutes: 10,
    example: "Запуск партнёрского кабинета",
    related: ["tasks", "documents"],
  },
  {
    moduleId: "marketplace",
    route: "/marketplace",
    purpose: "Маркетплейс и каталог",
    why: "Когда смотрите предложения и листинги",
    expectedResult: "Найден нужный листинг",
    workflow: "Маркетплейс → фильтр → открыть",
    difficulty: "средний",
    setupMinutes: 8,
    example: "Поиск предложения партнёра",
    related: ["crm", "analytics"],
  },
  {
    moduleId: "erp",
    route: "/erp",
    purpose: "ERP и операции",
    why: "Когда нужны склад, производство, операции",
    expectedResult: "Операционные данные по компании",
    workflow: "ERP → раздел → действие",
    difficulty: "сложный",
    setupMinutes: 30,
    example: "Статус производства",
    related: ["analytics", "projects"],
  },
];

export function helpForRoute(pathname: string): ModuleHelp | undefined {
  const base = (pathname.split("?")[0] || pathname).replace(/\/$/, "") || "/";
  const exact = MODULE_HELP_CATALOG.find((h) => h.route === base);
  if (exact) return exact;
  if (base.startsWith("/crm") || base === "/leads" || base === "/clients" || base === "/deals") {
    return MODULE_HELP_CATALOG.find((h) => h.moduleId === "crm");
  }
  if (base.startsWith("/identity")) {
    return MODULE_HELP_CATALOG.find((h) => h.moduleId === "profile");
  }
  if (base === "/reports") {
    return MODULE_HELP_CATALOG.find((h) => h.moduleId === "analytics");
  }
  return MODULE_HELP_CATALOG.find(
    (h) => base === h.route || base.startsWith(`${h.route}/`),
  );
}
