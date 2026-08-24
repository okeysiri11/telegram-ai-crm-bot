/**
 * Sprint 30.2 — Canonical Russian enterprise navigation.
 * Single source for sidebar, owner mode, roles, search categories, quick actions.
 */

export type RuNavItem = {
  id: string;
  label: string;
  route: string;
  icon?: string;
  ownerOnly?: boolean;
};

/** Primary sidebar — Sprint 30.2 / 30.7 Russian menu (every item → real module) */
export const ENTERPRISE_RU_SIDEBAR: RuNavItem[] = [
  { id: "home", label: "Главная", route: "/dashboard", icon: "dashboard" },
  { id: "workspace", label: "Рабочий стол", route: "/desktop", icon: "desktop" },
  { id: "city", label: "Город", route: "/city", icon: "city" },
  { id: "ai_agents", label: "AI-Агенты", route: "/ai-agents", icon: "ai_agents" },
  { id: "crm", label: "CRM", route: "/crm", icon: "crm" },
  { id: "erp", label: "ERP", route: "/erp", icon: "erp" },
  { id: "projects", label: "Проекты", route: "/projects", icon: "projects" },
  { id: "clients", label: "Клиенты", route: "/crm?view=clients", icon: "crm" },
  { id: "tasks", label: "Задачи", route: "/tasks", icon: "projects" },
  { id: "finance", label: "Финансы", route: "/analytics", icon: "analytics" },
  { id: "documents", label: "Документы", route: "/documents", icon: "documents" },
  { id: "knowledge", label: "Знания", route: "/knowledge", icon: "knowledge" },
  { id: "calendar", label: "Календарь", route: "/calendar", icon: "dashboard" },
  { id: "notifications", label: "Уведомления", route: "/notifications", icon: "dashboard" },
  { id: "production_studio", label: "Продакшн", route: "/production-studio", icon: "ai_studio" },
  { id: "marketplace", label: "Маркетплейс", route: "/marketplace", icon: "marketplace" },
  { id: "ai_studio", label: "Студия AI", route: "/ai-studio", icon: "ai_studio" },
  { id: "manufacturing", label: "Производство", route: "/erp?view=production", icon: "erp" },
  { id: "legal", label: "Юридический отдел", route: "/workspace/legal", icon: "security" },
  { id: "analytics", label: "Аналитика", route: "/analytics", icon: "analytics" },
  { id: "users", label: "Пользователи", route: "/identity/users", icon: "settings" },
  { id: "monitoring", label: "Мониторинг", route: "/health", icon: "dashboard" },
  { id: "settings", label: "Настройки", route: "/settings", icon: "settings" },
];

/** Owner Mode navigation */
export const OWNER_RU_NAV: RuNavItem[] = [
  { id: "owner_home", label: "Панель владельца", route: "/owner", icon: "dashboard", ownerOnly: true },
  { id: "owner_health", label: "Состояние платформы", route: "/health", icon: "dashboard", ownerOnly: true },
  { id: "owner_arch", label: "Архитектура", route: "/kernel", icon: "settings", ownerOnly: true },
  { id: "owner_audit", label: "Аудит", route: "/platform-builder/governance", icon: "security", ownerOnly: true },
  { id: "owner_security", label: "Центр безопасности", route: "/identity/security", icon: "security", ownerOnly: true },
  { id: "owner_ai", label: "Среда AI", route: "/ai-agents", icon: "ai_agents", ownerOnly: true },
  { id: "owner_kg", label: "Граф знаний", route: "/platform-builder/knowledge", icon: "knowledge", ownerOnly: true },
  { id: "owner_city", label: "Среда города", route: "/city", icon: "city", ownerOnly: true },
  { id: "owner_dev", label: "Разработчик", route: "/platform-builder/builder-studio", icon: "settings", ownerOnly: true },
  { id: "owner_logs", label: "Журналы", route: "/command-runtime", icon: "documents", ownerOnly: true },
  { id: "owner_flags", label: "Флаги функций", route: "/settings?tab=flags", icon: "settings", ownerOnly: true },
  { id: "owner_admin", label: "Администрирование", route: "/admin", icon: "settings", ownerOnly: true },
  { id: "owner_god", label: "Режим владельца", route: "/platform-builder/god-mode", icon: "dashboard", ownerOnly: true },
];

export type RoleSwitcherOption = {
  id: string;
  label: string;
  /** Maps to auth / first-entry role ids */
  roleIds: string[];
};

export const ROLE_SWITCHER_OPTIONS: RoleSwitcherOption[] = [
  { id: "owner", label: "Владелец", roleIds: ["owner", "platform_owner", "company_owner"] },
  { id: "administrator", label: "Администратор", roleIds: ["administrator", "admin", "system_admin"] },
  { id: "accountant", label: "Бухгалтер", roleIds: ["accountant", "auto_accountant", "agro_accountant"] },
  { id: "managing_partner", label: "Управляющий партнер", roleIds: ["managing_partner", "managing-partner"] },
  { id: "lawyer", label: "Юрист", roleIds: ["lawyer", "attorney"] },
  { id: "paralegal", label: "Помощник юриста", roleIds: ["paralegal", "legal_assistant"] },
  { id: "sales", label: "Продажи", roleIds: ["sales"] },
  { id: "support", label: "Поддержка", roleIds: ["support"] },
  { id: "employee", label: "Сотрудник", roleIds: ["employee"] },
  { id: "dealer", label: "Дилер", roleIds: ["dealer"] },
  { id: "partner", label: "Партнёр", roleIds: ["partner"] },
  { id: "client", label: "Клиент", roleIds: ["client"] },
  { id: "viewer", label: "Наблюдатель", roleIds: ["viewer", "read_only", "observer"] },
];

export const ORG_SELECTOR_OPTIONS = [
  { id: "ados", label: "ADOS Platform" },
  { id: "globefly", label: "GlobeFly" },
  { id: "crypto-desk", label: "Crypto Desk" },
  { id: "buildcorp", label: "BuildCorp" },
  { id: "skyfleet", label: "SkyFleet" },
  { id: "prime-auto", label: "Prime Auto" },
  { id: "lex", label: "Lex & Partners" },
  { id: "greenfield", label: "GreenField" },
  { id: "seller-co", label: "Seller Co" },
  { id: "demo-corp", label: "Demo Corp" },
  { id: "acme-ltd", label: "Acme Ltd" },
  { id: "bidex", label: "Bidex" },
];

export const SEARCH_CATEGORY_RU: Record<string, string> = {
  clients: "Клиенты",
  crm: "Клиенты",
  projects: "Проекты",
  documents: "Документы",
  ai_agents: "AI-Агенты",
  knowledge: "Знания",
  tasks: "Задачи",
  commands: "Команды",
  modules: "Модули",
  dashboards: "Панели",
  organizations: "Компании",
  users: "Пользователи",
  finance: "Финансы",
  erp: "ERP",
  workflows: "Процессы",
  marketplace: "Маркетинг",
  applications: "Приложения",
  reports: "Отчёты",
  hr: "HR",
  widgets: "Виджеты",
};

export const RU_QUICK_ACTIONS = [
  { id: "qa_module", label: "Открыть модуль", route: "/search", keywords: ["модуль", "открыть", "навигация"] },
  { id: "qa_client", label: "Открыть клиента", route: "/crm?view=clients", keywords: ["клиент", "открыть", "crm"] },
  { id: "qa_project", label: "Открыть проект", route: "/projects", keywords: ["проект", "открыть"] },
  { id: "qa_ai", label: "Открыть AI-агента", route: "/ai-agents", keywords: ["ai", "агент", "открыть"] },
  { id: "qa_create_client", label: "Создать клиента", route: "/crm?action=create_client", keywords: ["клиент", "создать", "crm"] },
  { id: "qa_create_project", label: "Создать проект", route: "/projects?action=create_project", keywords: ["проект", "создать"] },
  { id: "qa_doc", label: "Создать документ", route: "/documents?action=create_document", keywords: ["документ", "создать"] },
  { id: "qa_map", label: "Открыть карту", route: "/city", keywords: ["карта", "город"] },
  { id: "qa_task", label: "Создать задачу", route: "/tasks", keywords: ["задача", "создать"] },
  { id: "qa_palette", label: "Командная палитра", route: "/command-center", keywords: ["палитра", "команда", "ctrl"] },
];

/** Module id → Russian display label (shell overlay) */
export const MODULE_LABEL_RU: Record<string, string> = {
  dashboard: "Главная",
  desktop: "Рабочий стол",
  city: "Город",
  ai_agents: "AI-Агенты",
  ai_studio: "Студия AI",
  crm: "CRM",
  erp: "ERP",
  projects: "Проекты",
  documents: "Документы",
  knowledge: "Знания",
  analytics: "Аналитика",
  marketplace: "Маркетинг",
  production_studio: "Продакшн",
  settings: "Настройки",
  security: "Безопасность",
  automation: "Автоматизация",
  integrations: "Интеграции",
  business_network: "Бизнес-сеть",
  digital_citizens: "Цифровые граждане",
  life_engine: "Движок жизни",
  assets: "Активы",
  spatial: "Пространство",
  city_visualization: "Визуализация города",
  interactions: "Взаимодействия",
  intelligence: "Интеллект",
  orchestrator: "Оркестратор",
  kernel: "Ядро",
};

export const CATEGORY_LABEL_RU: Record<string, string> = {
  core: "Основное",
  business: "Бизнес",
  ai: "AI и продакшн",
  ops: "Операции",
  platform: "Платформа",
  system: "Система",
};

export const BREADCRUMB_LABEL_RU: Record<string, string> = {
  dashboard: "Главная",
  desktop: "Рабочий стол",
  "enterprise-city": "Город",
  city: "Город",
  "ai-agents": "AI-Агенты",
  "ai-studio": "AI-Студия",
  crm: "CRM",
  erp: "ERP",
  projects: "Проекты",
  documents: "Документы",
  knowledge: "Знания",
  analytics: "Аналитика",
  marketplace: "Маркетинг",
  "production-studio": "Продакшн",
  settings: "Настройки",
  security: "Безопасность",
  identity: "Идентичность",
  profile: "Профиль",
  sessions: "Сессии",
  mfa: "MFA",
  owner: "Панель владельца",
  workspace: "Рабочее пространство",
  finance: "Финансы",
  legal: "Юридический отдел",
  search: "Поиск",
  "platform-builder": "Конструктор",
  "mission-control": "Мониторинг",
  runtime: "AI Runtime",
  governance: "Аудит",
  "builder-studio": "Студия",
  "command-center": "Командный центр",
  "command-runtime": "Журналы",
  kernel: "Архитектура",
  automation: "Автоматизация",
  integrations: "Интеграции",
  onboarding: "Онбординг",
  "first-entry": "Первый вход",
  users: "Пользователи",
  organizations: "Компании",
  portals: "Порталы",
  calendar: "Календарь",
  notifications: "Уведомления",
  tasks: "Задачи",
  admin: "Администрирование",
  health: "Здоровье",
  dashboards: "Панели",
  client: "Клиент",
  dealer: "Дилер",
  "god-mode": "Режим владельца",
};
