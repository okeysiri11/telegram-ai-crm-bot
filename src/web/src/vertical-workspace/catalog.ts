/**
 * Sprint 42.8 — каталог вертикальных рабочих пространств (RU-first).
 * Единый шаблон: навигация · дашборд · AI-гид · специалисты · действия.
 */

import type { VerticalDef } from "./types";

function path(verticalId: string, sectionId = "home"): string {
  if (sectionId === "home") return `/vertical/${verticalId}`;
  return `/vertical/${verticalId}/${sectionId}`;
}

export const VERTICAL_WORKSPACES: VerticalDef[] = [
  {
    id: "owner",
    label: "Owner",
    purpose: "Центр управления предприятием",
    route: path("owner"),
    legacyRoute: "/dashboard",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "strategy", label: "Стратегия" },
      { id: "finance", label: "Финансы" },
      { id: "team", label: "Команда" },
      { id: "ai", label: "AI-команда" },
      { id: "reports", label: "Отчёты" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "strategy", name: "Стратег", role: "Приоритеты и цели" },
      { id: "finance", name: "Финансист", role: "Касса и прогноз" },
      { id: "ops", name: "Операции", role: "Контроль процессов" },
    ],
    stats: [
      { label: "Активные модули", value: "12" },
      { label: "Задачи сегодня", value: "7" },
      { label: "Уведомления", value: "4" },
    ],
    quickActions: [
      { label: "Открыть панель", route: "/dashboard" },
      { label: "Команда AI", route: "/platform-builder/ai-team" },
      { label: "Настройки", route: "/settings" },
    ],
    recommendations: [
      "Просмотрите сводку по вертикалям",
      "Закройте просроченные задачи руководства",
      "Проверьте статус AI Консьержа",
    ],
    primaryAction: { label: "Открыть панель управления", route: "/dashboard" },
    recentObjects: [
      { title: "Сводка недели", detail: "Готова к просмотру", route: "/dashboard" },
      { title: "Команда AI", detail: "3 специалиста онлайн", route: "/platform-builder/ai-team" },
    ],
    events: [
      { title: "Обновлена стратегия", detail: "2 часа назад" },
      { title: "Новый отчёт финансов", detail: "Сегодня" },
    ],
    tasks: [
      { title: "Утвердить приоритеты", status: "В работе" },
      { title: "Проверить кассу", status: "Ожидает" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: [
        "7 задач требуют внимания руководства",
        "4 уведомления по платформе",
        "Команда AI готова к работе",
      ],
      recommendedAction: { label: "Открыть панель управления", route: "/dashboard" },
    },
  },
  {
    id: "crm",
    label: "CRM",
    purpose: "Клиенты, сделки и коммуникации",
    route: path("crm"),
    legacyRoute: "/crm",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "clients", label: "Клиенты", href: "/crm?view=clients" },
      { id: "deals", label: "Сделки", href: "/crm?view=deals" },
      { id: "leads", label: "Лиды", href: "/crm?view=leads" },
      { id: "contacts", label: "Контакты", href: "/crm?view=contacts" },
      { id: "comms", label: "Коммуникации", href: "/crm?view=communications" },
      { id: "reports", label: "Отчёты", href: "/crm?view=reports" },
      { id: "ai", label: "AI CRM" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "sales", name: "Менеджер продаж", role: "Сделки и follow-up" },
      { id: "deals", name: "Контроль сделок", role: "Воронка и риски" },
      { id: "leads", name: "Квалификация лидов", role: "Новые обращения" },
      { id: "clients", name: "Анализ клиентов", role: "Сегменты и ценность" },
    ],
    stats: [
      { label: "Лиды", value: "5" },
      { label: "Сделки", value: "12" },
      { label: "Просрочено", value: "2" },
    ],
    quickActions: [
      { label: "Создать клиента", route: "/crm?view=clients&action=create" },
      { label: "Новая сделка", route: "/crm?view=deals&action=create" },
      { label: "Открыть лиды", route: "/crm?view=leads" },
    ],
    recommendations: [
      "Квалифицируйте 5 новых лидов",
      "Закройте 2 просроченные сделки",
      "Обновите статусы коммуникаций",
    ],
    primaryAction: { label: "Создать клиента", route: "/crm?view=clients&action=create" },
    recentObjects: [
      { title: "Acme Travel", detail: "Клиент · активен", route: "/crm?view=clients" },
      { title: "Корпоративные билеты", detail: "Лид · новый", route: "/crm?view=leads" },
    ],
    events: [
      { title: "Новый лид", detail: "Корпоративные билеты" },
      { title: "Сделка обновлена", detail: "Подписка B2B" },
    ],
    tasks: [
      { title: "Позвонить клиенту Acme", status: "Сегодня" },
      { title: "Обновить воронку", status: "На неделе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["5 новых лидов", "2 просроченные задачи", "1 договор ожидает согласования"],
      recommendedAction: { label: "Открыть лиды", route: "/crm?view=leads" },
    },
  },
  {
    id: "auto",
    label: "Auto",
    purpose: "Автомобили, импорт, продажи и VIN",
    route: path("auto"),
    legacyRoute: "/workspace/auto",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "cars", label: "Автомобили" },
      { id: "import", label: "Импорт" },
      { id: "buyers", label: "Покупатели" },
      { id: "sales", label: "Продажи" },
      { id: "vin", label: "VIN" },
      { id: "warehouse", label: "Склад" },
      { id: "docs", label: "Документы" },
      { id: "finance", label: "Финансы" },
      { id: "ai", label: "AI Auto" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "vin", name: "Проверка VIN", role: "История и риски" },
      { id: "appraisal", name: "Оценка автомобиля", role: "Рыночная цена" },
      { id: "match", name: "Подбор автомобиля", role: "Запросы клиентов" },
      { id: "import", name: "Контроль импорта", role: "Поставки и сроки" },
      { id: "profit", name: "Расчёт прибыли", role: "Маржа и касса" },
    ],
    stats: [
      { label: "На складе", value: "48" },
      { label: "В пути", value: "6" },
      { label: "Сделки месяца", value: "11" },
    ],
    quickActions: [
      { label: "Проверить VIN", route: path("auto", "vin") },
      { label: "Добавить автомобиль", route: path("auto", "cars") },
      { label: "Открыть склад", route: path("auto", "warehouse") },
    ],
    recommendations: [
      "Проверьте VIN у 3 новых поступлений",
      "Закройте импорт с задержкой",
      "Подготовьте подбор для горячего клиента",
    ],
    primaryAction: { label: "Проверить VIN", route: path("auto", "vin") },
    recentObjects: [
      { title: "BMW X5 · 2021", detail: "Склад · готов", route: path("auto", "cars") },
      { title: "Партия KR-08", detail: "Импорт · в пути", route: path("auto", "import") },
    ],
    events: [
      { title: "VIN проверен", detail: "Toyota Camry" },
      { title: "Оценка обновлена", detail: "Mercedes E-Class" },
    ],
    tasks: [
      { title: "Приёмка партии", status: "Сегодня" },
      { title: "Расчёт маржи", status: "В работе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: [
        "6 автомобилей в пути",
        "3 VIN без полной проверки",
        "11 продаж за месяц — выше плана",
      ],
      recommendedAction: { label: "Проверить VIN", route: path("auto", "vin") },
    },
  },
  {
    id: "crypto",
    label: "Crypto OTC",
    purpose: "Сделки OTC, кошельки, AML и курсы",
    route: path("crypto"),
    legacyRoute: "/workspace/crypto",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "deals", label: "Сделки OTC" },
      { id: "wallets", label: "Кошельки" },
      { id: "rates", label: "Курсы" },
      { id: "clients", label: "Клиенты" },
      { id: "aml", label: "AML" },
      { id: "payments", label: "Платежи" },
      { id: "history", label: "История" },
      { id: "ai", label: "AI Crypto" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "aml", name: "Контроль AML", role: "Проверки и риски" },
      { id: "arb", name: "Поиск арбитража", role: "Спреды и окна" },
      { id: "risk", name: "Контроль рисков", role: "Лимиты и алерты" },
      { id: "rates", name: "Мониторинг курсов", role: "Рынок в реальном времени" },
      { id: "liq", name: "Контроль ликвидности", role: "Касса и остатки" },
    ],
    stats: [
      { label: "Сделки сегодня", value: "9" },
      { label: "AML на проверке", value: "2" },
      { label: "Спред", value: "0,18%" },
    ],
    quickActions: [
      { label: "Новая OTC-сделка", route: path("crypto", "deals") },
      { label: "Проверка AML", route: path("crypto", "aml") },
      { label: "Курсы", route: path("crypto", "rates") },
    ],
    recommendations: [
      "Закройте 2 проверки AML",
      "Проверьте арбитражное окно BTC/USDT",
      "Сверьте ликвидность кошельков",
    ],
    primaryAction: { label: "Создать OTC-сделку", route: path("crypto", "deals") },
    recentObjects: [
      { title: "OTC · BTC 1.2", detail: "В исполнении", route: path("crypto", "deals") },
      { title: "Клиент · North Desk", detail: "AML · ожидает", route: path("crypto", "aml") },
    ],
    events: [
      { title: "Курс обновлён", detail: "USDT" },
      { title: "Платёж подтверждён", detail: "Сделка #4821" },
    ],
    tasks: [
      { title: "AML по North Desk", status: "Срочно" },
      { title: "Сверка кошельков", status: "Сегодня" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["2 AML-проверки ждут решения", "Арбитражное окно открыто 12 минут", "Ликвидность в норме"],
      recommendedAction: { label: "Открыть AML", route: path("crypto", "aml") },
    },
  },
  {
    id: "travel",
    label: "Travel",
    purpose: "Туры, бронирования, отели и авиабилеты",
    route: path("travel"),
    nav: [
      { id: "home", label: "Обзор" },
      { id: "tours", label: "Туры" },
      { id: "bookings", label: "Бронирования" },
      { id: "clients", label: "Клиенты" },
      { id: "hotels", label: "Отели" },
      { id: "flights", label: "Авиабилеты" },
      { id: "docs", label: "Документы" },
      { id: "payments", label: "Платежи" },
      { id: "ai", label: "AI Travel" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "tour", name: "Подбор тура", role: "Маршруты и пакеты" },
      { id: "tickets", name: "Подбор билетов", role: "Авиа и стыковки" },
      { id: "hotel", name: "Подбор гостиницы", role: "Размещение" },
      { id: "docs", name: "Контроль документов", role: "Визы и пакеты" },
    ],
    stats: [
      { label: "Брони сегодня", value: "14" },
      { label: "Туры в работе", value: "6" },
      { label: "Документы", value: "3" },
    ],
    quickActions: [
      { label: "Подобрать тур", route: path("travel", "tours") },
      { label: "Новое бронирование", route: path("travel", "bookings") },
      { label: "Проверить документы", route: path("travel", "docs") },
    ],
    recommendations: [
      "Закройте 3 пакета документов",
      "Подтвердите отели на ближайшие выезды",
      "Проверьте оплату по 2 бронированиям",
    ],
    primaryAction: { label: "Подобрать тур", route: path("travel", "tours") },
    recentObjects: [
      { title: "Тур · Греция 7 ночей", detail: "Семья Ивановых", route: path("travel", "tours") },
      { title: "Бронь · Hotel Azure", detail: "Ожидает оплату", route: path("travel", "bookings") },
    ],
    events: [
      { title: "Билеты выписаны", detail: "Рейс SU 112" },
      { title: "Виза готова", detail: "Клиент Петров" },
    ],
    tasks: [
      { title: "Собрать документы", status: "Сегодня" },
      { title: "Подтвердить отель", status: "В работе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["14 бронирований сегодня", "3 пакета документов ждут проверки", "6 туров в активной сборке"],
      recommendedAction: { label: "Подобрать тур", route: path("travel", "tours") },
    },
  },
  {
    id: "drone",
    label: "Drone",
    purpose: "Проекты, аппараты, полёты и производство",
    route: path("drone"),
    legacyRoute: "/workspace/drone",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "projects", label: "Проекты" },
      { id: "units", label: "Аппараты" },
      { id: "flights", label: "Полёты" },
      { id: "missions", label: "Миссии" },
      { id: "production", label: "Производство" },
      { id: "team", label: "Команда" },
      { id: "warehouse", label: "Склад" },
      { id: "tests", label: "Испытания" },
      { id: "ai", label: "AI Drone" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "engineer", name: "Инженер", role: "Конструкции и системы" },
      { id: "designer", name: "Конструктор", role: "Чертежи и узлы" },
      { id: "architect", name: "Проектировщик", role: "Миссии и схемы" },
      { id: "prod", name: "Контроль производства", role: "Сборка и качество" },
    ],
    stats: [
      { label: "Аппараты", value: "22" },
      { label: "Миссии", value: "5" },
      { label: "Испытания", value: "3" },
    ],
    quickActions: [
      { label: "Новая миссия", route: path("drone", "missions") },
      { label: "План полёта", route: path("drone", "flights") },
      { label: "Производство", route: path("drone", "production") },
    ],
    recommendations: [
      "Завершите 3 протокола испытаний",
      "Проверьте склад комплектующих",
      "Обновите статус сборки серии D-4",
    ],
    primaryAction: { label: "Создать миссию", route: path("drone", "missions") },
    recentObjects: [
      { title: "Миссия · Картография", detail: "План готов", route: path("drone", "missions") },
      { title: "Аппарат D-4", detail: "Сборка 80%", route: path("drone", "production") },
    ],
    events: [
      { title: "Полёт завершён", detail: "Полигон Север" },
      { title: "Испытание ОК", detail: "Серия D-4" },
    ],
    tasks: [
      { title: "Протокол испытания", status: "Сегодня" },
      { title: "Комплектация склада", status: "В работе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["5 миссий в плане", "3 испытания без протокола", "Сборка D-4 на финальном этапе"],
      recommendedAction: { label: "Открыть испытания", route: path("drone", "tests") },
    },
  },
  {
    id: "agro",
    label: "Agro",
    purpose: "Поля, техника, посевы и урожай",
    route: path("agro"),
    legacyRoute: "/workspace/agro",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "fields", label: "Поля" },
      { id: "machinery", label: "Техника" },
      { id: "crops", label: "Посевы" },
      { id: "harvest", label: "Урожай" },
      { id: "irrigation", label: "Полив" },
      { id: "warehouse", label: "Склад" },
      { id: "works", label: "Работы" },
      { id: "ai", label: "AI Agro" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "agronomist", name: "Агроном", role: "Посевы и уход" },
      { id: "yield", name: "Аналитик урожая", role: "Прогноз и факты" },
      { id: "fleet", name: "Контроль техники", role: "Парк и ремонты" },
      { id: "weather", name: "Погодный помощник", role: "Окна работ" },
    ],
    stats: [
      { label: "Поля", value: "18" },
      { label: "Техника в работе", value: "7" },
      { label: "Работы сегодня", value: "4" },
    ],
    quickActions: [
      { label: "План работ", route: path("agro", "works") },
      { label: "Статус полей", route: path("agro", "fields") },
      { label: "Полив", route: path("agro", "irrigation") },
    ],
    recommendations: [
      "Учтите окно полива на ближайшие 48 часов",
      "Проверьте технику перед посевной сменой",
      "Обновите прогноз урожая по южным полям",
    ],
    primaryAction: { label: "Открыть план работ", route: path("agro", "works") },
    recentObjects: [
      { title: "Поле Юг-3", detail: "Полив запланирован", route: path("agro", "fields") },
      { title: "Комбайн К-7", detail: "ТО через 2 дня", route: path("agro", "machinery") },
    ],
    events: [
      { title: "Посев завершён", detail: "Участок Север" },
      { title: "Прогноз погоды", detail: "Дождь завтра" },
    ],
    tasks: [
      { title: "Полив Юг-3", status: "Сегодня" },
      { title: "ТО комбайна", status: "На неделе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["Окно полива открыто на 48 часов", "7 единиц техники в поле", "Прогноз урожая обновлён"],
      recommendedAction: { label: "Открыть полив", route: path("agro", "irrigation") },
    },
  },
  {
    id: "construction",
    label: "Construction",
    purpose: "Объекты, сметы, подрядчики и материалы",
    route: path("construction"),
    nav: [
      { id: "home", label: "Обзор" },
      { id: "sites", label: "Объекты" },
      { id: "projects", label: "Проекты" },
      { id: "contractors", label: "Подрядчики" },
      { id: "estimates", label: "Сметы" },
      { id: "materials", label: "Материалы" },
      { id: "machinery", label: "Техника" },
      { id: "docs", label: "Документы" },
      { id: "ai", label: "AI Construction" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "foreman", name: "Прораб", role: "Объект и смена" },
      { id: "engineer", name: "Инженер", role: "Техрешения" },
      { id: "estimator", name: "Сметчик", role: "Сметы и объёмы" },
      { id: "buyer", name: "Закупщик", role: "Материалы и поставки" },
      { id: "budget", name: "Контроль бюджета", role: "Лимиты и отклонения" },
    ],
    stats: [
      { label: "Объекты", value: "9" },
      { label: "Сметы на согласовании", value: "4" },
      { label: "Отклонение бюджета", value: "−2,1%" },
    ],
    quickActions: [
      { label: "Новая смета", route: path("construction", "estimates") },
      { label: "Объекты", route: path("construction", "sites") },
      { label: "Материалы", route: path("construction", "materials") },
    ],
    recommendations: [
      "Согласуйте 4 сметы",
      "Проверьте поставку материалов на объект «Река»",
      "Сверьте бюджет по подрядчикам",
    ],
    primaryAction: { label: "Открыть сметы", route: path("construction", "estimates") },
    recentObjects: [
      { title: "Объект «Река»", detail: "Смета на согласовании", route: path("construction", "sites") },
      { title: "Подрядчик СтройМост", detail: "Акт ожидает", route: path("construction", "contractors") },
    ],
    events: [
      { title: "Поставка бетона", detail: "Объект Река" },
      { title: "Смета обновлена", detail: "Корпус B" },
    ],
    tasks: [
      { title: "Согласовать смету", status: "Срочно" },
      { title: "Приёмка материалов", status: "Сегодня" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["4 сметы ждут согласования", "Бюджет в пределах −2,1%", "Поставка на объект «Река» сегодня"],
      recommendedAction: { label: "Открыть сметы", route: path("construction", "estimates") },
    },
  },
  {
    id: "production",
    label: "Production",
    purpose: "Заказы, производство, качество и склад",
    route: path("production"),
    nav: [
      { id: "home", label: "Обзор" },
      { id: "orders", label: "Заказы" },
      { id: "factory", label: "Производство" },
      { id: "equipment", label: "Оборудование" },
      { id: "warehouse", label: "Склад" },
      { id: "quality", label: "Качество" },
      { id: "suppliers", label: "Поставщики" },
      { id: "ai", label: "AI Factory" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "prod", name: "Контроль производства", role: "Линии и смены" },
      { id: "qa", name: "Контроль качества", role: "Брак и протоколы" },
      { id: "planner", name: "Планировщик", role: "Заказы и сроки" },
      { id: "load", name: "Оптимизация загрузки", role: "Мощности" },
    ],
    stats: [
      { label: "Заказы в работе", value: "16" },
      { label: "Загрузка линий", value: "78%" },
      { label: "Брак", value: "0,4%" },
    ],
    quickActions: [
      { label: "План смены", route: path("production", "factory") },
      { label: "Заказы", route: path("production", "orders") },
      { label: "Качество", route: path("production", "quality") },
    ],
    recommendations: [
      "Сбалансируйте загрузку линии 2",
      "Закройте 3 протокола качества",
      "Проверьте поставку комплектующих",
    ],
    primaryAction: { label: "Открыть производство", route: path("production", "factory") },
    recentObjects: [
      { title: "Заказ #904", detail: "Сборка · 60%", route: path("production", "orders") },
      { title: "Линия 2", detail: "Загрузка 92%", route: path("production", "factory") },
    ],
    events: [
      { title: "Партия принята", detail: "СК-12" },
      { title: "Контроль качества", detail: "Пройден" },
    ],
    tasks: [
      { title: "План смены", status: "Сегодня" },
      { title: "Протокол качества", status: "В работе" },
    ],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["Загрузка линий 78%", "16 заказов в работе", "Брак ниже нормы"],
      recommendedAction: { label: "Открыть производство", route: path("production", "factory") },
    },
  },
  {
    id: "knowledge",
    label: "Knowledge",
    purpose: "База знаний, статьи и регламенты",
    route: path("knowledge"),
    legacyRoute: "/knowledge",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "articles", label: "Статьи", href: "/knowledge" },
      { id: "guides", label: "Регламенты" },
      { id: "search", label: "Поиск", href: "/search" },
      { id: "ai", label: "AI Knowledge" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "librarian", name: "Хранитель знаний", role: "Статьи и актуальность" },
      { id: "search", name: "Поиск по знаниям", role: "Быстрые ответы" },
    ],
    stats: [
      { label: "Статьи", value: "128" },
      { label: "Обновлено за неделю", value: "9" },
      { label: "Запросы AI", value: "34" },
    ],
    quickActions: [
      { label: "Открыть базу знаний", route: "/knowledge" },
      { label: "Поиск", route: "/search" },
    ],
    recommendations: [
      "Обновите устаревшие регламенты",
      "Добавьте ответы на частые вопросы",
    ],
    primaryAction: { label: "Открыть базу знаний", route: "/knowledge" },
    recentObjects: [
      { title: "Регламент возвратов", detail: "Обновлён вчера", route: "/knowledge" },
    ],
    events: [{ title: "Новая статья", detail: "Онбординг менеджера" }],
    tasks: [{ title: "Актуализировать FAQ", status: "На неделе" }],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["9 статей обновлены за неделю", "34 AI-запроса к базе знаний"],
      recommendedAction: { label: "Открыть базу знаний", route: "/knowledge" },
    },
  },
  {
    id: "documents",
    label: "Documents",
    purpose: "Документы, согласования и архив",
    route: path("documents"),
    legacyRoute: "/documents",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "inbox", label: "Входящие" },
      { id: "approvals", label: "Согласования" },
      { id: "archive", label: "Архив" },
      { id: "ai", label: "AI Documents" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "clerk", name: "Делопроизводитель", role: "Маршруты документов" },
      { id: "review", name: "Проверка документов", role: "Ошибки и полнота" },
    ],
    stats: [
      { label: "На согласовании", value: "8" },
      { label: "Новые сегодня", value: "5" },
      { label: "Просрочено", value: "1" },
    ],
    quickActions: [
      { label: "Согласования", route: path("documents", "approvals") },
      { label: "Архив", route: path("documents", "archive") },
    ],
    recommendations: [
      "Закройте 1 просроченное согласование",
      "Разберите входящие за сегодня",
    ],
    primaryAction: { label: "Открыть согласования", route: path("documents", "approvals") },
    recentObjects: [
      { title: "Договор поставки", detail: "Ожидает подписи", route: path("documents", "approvals") },
    ],
    events: [{ title: "Документ согласован", detail: "Акт выполненных работ" }],
    tasks: [{ title: "Подписать договор", status: "Срочно" }],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["8 документов на согласовании", "1 просроченное согласование"],
      recommendedAction: { label: "Открыть согласования", route: path("documents", "approvals") },
    },
  },
  {
    id: "marketplace",
    label: "Marketplace",
    purpose: "Магазин решений и установки",
    route: path("marketplace"),
    legacyRoute: "/marketplace",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "catalog", label: "Каталог", href: "/marketplace" },
      { id: "installed", label: "Установлено" },
      { id: "ai", label: "AI Marketplace" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "curator", name: "Куратор решений", role: "Подбор модулей" },
    ],
    stats: [
      { label: "Доступно", value: "24" },
      { label: "Установлено", value: "7" },
    ],
    quickActions: [
      { label: "Открыть магазин", route: "/marketplace" },
    ],
    recommendations: [
      "Просмотрите рекомендованные решения для вашей отрасли",
    ],
    primaryAction: { label: "Открыть магазин решений", route: "/marketplace" },
    recentObjects: [
      { title: "Пакет CRM+", detail: "Рекомендован", route: "/marketplace" },
    ],
    events: [{ title: "Установлен модуль", detail: "Аналитика продаж" }],
    tasks: [{ title: "Оценить пакет CRM+", status: "На неделе" }],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["24 решения доступны", "7 уже установлены"],
      recommendedAction: { label: "Открыть магазин", route: "/marketplace" },
    },
  },
  {
    id: "ai_studio",
    label: "AI Studio",
    purpose: "Создание и настройка AI-команды",
    route: path("ai_studio"),
    legacyRoute: "/platform-builder/builder-studio",
    nav: [
      { id: "home", label: "Обзор" },
      { id: "concierge", label: "AI Консьерж", href: "/platform-builder/concierge" },
      { id: "team", label: "Команда AI", href: "/platform-builder/ai-team" },
      { id: "wizard", label: "Мастер агента", href: "/platform-builder/builder-studio?mode=wizard" },
      { id: "ai", label: "Студия" },
    ],
    agents: [
      { id: "concierge", name: "AI Консьерж", role: "Главный помощник" },
      { id: "builder", name: "Конструктор агентов", role: "Сборка специалистов" },
      { id: "trainer", name: "Наставник", role: "Стили и навыки" },
    ],
    stats: [
      { label: "Агенты", value: "8" },
      { label: "Активны", value: "6" },
      { label: "На паузе", value: "2" },
    ],
    quickActions: [
      { label: "Создать агента", route: "/platform-builder/builder-studio?mode=wizard" },
      { label: "Настроить консьержа", route: "/platform-builder/concierge" },
      { label: "Команда AI", route: "/platform-builder/ai-team" },
    ],
    recommendations: [
      "Завершите настройку AI Консьержа",
      "Добавьте специалиста для активной вертикали",
    ],
    primaryAction: {
      label: "Открыть студию AI",
      route: "/platform-builder/builder-studio",
    },
    recentObjects: [
      {
        title: "AI Консьерж",
        detail: "Готов к работе",
        route: "/platform-builder/concierge",
      },
    ],
    events: [{ title: "Агент создан", detail: "Менеджер продаж" }],
    tasks: [{ title: "Настроить права агента", status: "В работе" }],
    aiGuide: {
      greeting: "Добро пожаловать.",
      bullets: ["8 агентов в организации", "Консьерж готов помогать", "2 специалиста на паузе"],
      recommendedAction: {
        label: "Открыть студию AI",
        route: "/platform-builder/builder-studio",
      },
    },
  },
];

export const VERTICAL_BY_ID: Record<string, VerticalDef> = Object.fromEntries(
  VERTICAL_WORKSPACES.map((v) => [v.id, v]),
);

export function getVertical(id: string): VerticalDef | undefined {
  return VERTICAL_BY_ID[id];
}

export function verticalHomePath(id: string): string {
  return getVertical(id)?.route || `/vertical/${id}`;
}

export function sectionPath(verticalId: string, sectionId: string): string {
  const v = getVertical(verticalId);
  const item = v?.nav.find((n) => n.id === sectionId);
  if (item?.href) return item.href;
  return path(verticalId, sectionId);
}
