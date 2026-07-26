/**
 * Enterprise Integration Hub catalog — Sprint 33.1.
 * Declarative cards over existing hubIntegrations / notifications / routes.
 * No new Integration Engine / API Gateway / AI Core.
 */

export type IntegrationCategory = "communication" | "business" | "developer";

export type IntegrationStatus =
  | "active"
  | "needs_setup"
  | "error"
  | "idle"
  | "draft";

export type IntegrationDef = {
  id: string;
  title: string;
  category: IntegrationCategory;
  description: string;
  /** Existing hub / API prefix key or path hint (presentation). */
  hubKey?: string;
  healthHint?: string;
  route?: string;
  processes: string[];
  aiAgents: string[];
  defaultStatus: IntegrationStatus;
  wizardSteps: string[];
};

export const INTEGRATION_CATEGORIES: Array<{ id: IntegrationCategory | "all"; label: string }> = [
  { id: "all", label: "Все" },
  { id: "communication", label: "Communication" },
  { id: "business", label: "Business" },
  { id: "developer", label: "Developer" },
];

/** Communication — reuse Notification Center / comms infrastructure. */
export const COMMUNICATION_INTEGRATIONS: IntegrationDef[] = [
  {
    id: "telegram",
    title: "Telegram",
    category: "communication",
    description: "Messaging channel через существующий bot / notifications.",
    hubKey: "notifications",
    healthHint: "/api/enterprise-comms/v1",
    route: "/workspace/ai",
    processes: ["Lead intake", "Client alerts"],
    aiAgents: ["Concierge", "Sales Ops"],
    defaultStatus: "active",
    wizardSteps: ["Выбор канала", "Bot token / chat", "Проверка доставки", "Активация"],
  },
  {
    id: "whatsapp",
    title: "WhatsApp",
    category: "communication",
    description: "Business messaging поверх Notification Center.",
    hubKey: "notifications",
    healthHint: "/api/enterprise-comms/v1",
    route: "/settings",
    processes: ["Support triage"],
    aiAgents: ["Support Agent"],
    defaultStatus: "needs_setup",
    wizardSteps: ["Провайдер", "Business number", "Webhook", "Тест сообщения"],
  },
  {
    id: "email",
    title: "Email",
    category: "communication",
    description: "Transactional / outreach email.",
    hubKey: "notifications",
    route: "/settings",
    processes: ["Invoice send", "Onboarding"],
    aiAgents: ["Concierge"],
    defaultStatus: "active",
    wizardSteps: ["SMTP / provider", "From domain", "Templates", "Тест"],
  },
  {
    id: "sms",
    title: "SMS",
    category: "communication",
    description: "OTP и alerts через comms.",
    hubKey: "notifications",
    route: "/settings",
    processes: ["MFA", "Reminders"],
    aiAgents: ["Ops Copilot"],
    defaultStatus: "needs_setup",
    wizardSteps: ["Провайдер", "Sender ID", "Лимиты", "Тест SMS"],
  },
  {
    id: "web_widget",
    title: "Web Widget",
    category: "communication",
    description: "Встраиваемый чат / capture на сайте.",
    hubKey: "webFoundation",
    route: "/platform-builder/experience",
    processes: ["Lead capture"],
    aiAgents: ["Concierge"],
    defaultStatus: "draft",
    wizardSteps: ["Домен", "Тема виджета", "Маршрутизация AI", "Embed код"],
  },
  {
    id: "push",
    title: "Push Notifications",
    category: "communication",
    description: "In-app / push поверх Notification Center.",
    hubKey: "notifications",
    route: "/command-center",
    processes: ["Task alerts", "AI briefs"],
    aiAgents: ["Concierge"],
    defaultStatus: "active",
    wizardSteps: ["Канал", "Права устройства", "Сегменты", "Тест push"],
  },
];

export const BUSINESS_INTEGRATIONS: IntegrationDef[] = [
  {
    id: "crm",
    title: "CRM",
    category: "business",
    description: "CRM workspace и pipeline sync.",
    hubKey: "commerceCore",
    route: "/workspace/crm",
    processes: ["Pipeline", "Deals"],
    aiAgents: ["Sales Ops"],
    defaultStatus: "active",
    wizardSteps: ["Система CRM", "Маппинг полей", "Синхронизация", "Готово"],
  },
  {
    id: "erp",
    title: "ERP",
    category: "business",
    description: "ERP / inventory связь.",
    route: "/workspace/erp",
    processes: ["Inventory", "Orders"],
    aiAgents: ["Ops Copilot"],
    defaultStatus: "needs_setup",
    wizardSteps: ["ERP система", "Склады", "Синхронизация", "Валидация"],
  },
  {
    id: "accounting",
    title: "Accounting",
    category: "business",
    description: "Учёт и проводки.",
    hubKey: "financeIntegration",
    healthHint: "/api/finance-int/v1",
    route: "/workspace/finance",
    processes: ["Journal", "Close"],
    aiAgents: ["Finance Agent"],
    defaultStatus: "needs_setup",
    wizardSteps: ["План счетов", "Период", "Импорт", "Сверка"],
  },
  {
    id: "payments",
    title: "Payment Systems",
    category: "business",
    description: "Платежи и биллинг.",
    hubKey: "financePayments",
    route: "/workspace/finance",
    processes: ["Checkout", "Refunds"],
    aiAgents: ["Finance Agent"],
    defaultStatus: "idle",
    wizardSteps: ["Провайдер", "Ключи", "Webhook оплаты", "Тестовый платёж"],
  },
  {
    id: "documents",
    title: "Document Management",
    category: "business",
    description: "Документы и Knowledge.",
    hubKey: "knowledgeGraph",
    route: "/platform-builder/knowledge",
    processes: ["Doc intake", "Contracts"],
    aiAgents: ["Knowledge Agent"],
    defaultStatus: "active",
    wizardSteps: ["Хранилище", "Права", "Индексация", "Проверка"],
  },
  {
    id: "calendar",
    title: "Calendar",
    category: "business",
    description: "Календарь встреч / booking.",
    route: "/workspace",
    processes: ["Scheduling"],
    aiAgents: ["Concierge"],
    defaultStatus: "draft",
    wizardSteps: ["Календарь", "Часовой пояс", "Слоты", "Синхронизация"],
  },
  {
    id: "storage",
    title: "Storage",
    category: "business",
    description: "Файловое хранилище.",
    hubKey: "secretsVault",
    route: "/workspace/docs",
    processes: ["File sync"],
    aiAgents: ["Ops Copilot"],
    defaultStatus: "idle",
    wizardSteps: ["Bucket / drive", "Права", "Пути", "Тест upload"],
  },
];

export const DEVELOPER_INTEGRATIONS: IntegrationDef[] = [
  {
    id: "rest_api",
    title: "REST API",
    category: "developer",
    description: "Существующие REST префиксы платформы.",
    hubKey: "enterpriseHub",
    route: "/platform-builder",
    processes: ["External sync"],
    aiAgents: ["Ops Copilot"],
    defaultStatus: "active",
    wizardSteps: ["Базовый URL", "Auth", "Scopes", "Smoke test"],
  },
  {
    id: "webhooks",
    title: "Webhooks",
    category: "developer",
    description: "Исходящие события (presentation over workflows).",
    hubKey: "workflow",
    route: "/platform-builder/workflow-center",
    processes: ["Event fan-out"],
    aiAgents: ["Automation"],
    defaultStatus: "needs_setup",
    wizardSteps: ["Endpoint", "Secret", "События", "Retry policy"],
  },
  {
    id: "oauth",
    title: "OAuth",
    category: "developer",
    description: "OAuth / ISAM identity.",
    hubKey: "authentication",
    healthHint: "/api/enterprise-isam/v1",
    route: "/identity",
    processes: ["SSO"],
    aiAgents: ["Concierge"],
    defaultStatus: "active",
    wizardSteps: ["Client ID", "Redirect URI", "Scopes", "Проверка login"],
  },
  {
    id: "api_keys",
    title: "API Keys",
    category: "developer",
    description: "Ключи доступа (vault / secrets).",
    hubKey: "secretsVault",
    route: "/settings",
    processes: ["Partner API"],
    aiAgents: ["Ops Copilot"],
    defaultStatus: "needs_setup",
    wizardSteps: ["Имя ключа", "Права", "Ротация", "Сохранить"],
  },
  {
    id: "sdk",
    title: "SDK",
    category: "developer",
    description: "Builder SDK / client libraries.",
    hubKey: "webFoundation",
    route: "/platform-builder/builder-studio",
    processes: ["Embed integrations"],
    aiAgents: ["Builder"],
    defaultStatus: "draft",
    wizardSteps: ["Язык SDK", "Пакет", "Пример", "Publish"],
  },
];

export const ALL_INTEGRATIONS: IntegrationDef[] = [
  ...COMMUNICATION_INTEGRATIONS,
  ...BUSINESS_INTEGRATIONS,
  ...DEVELOPER_INTEGRATIONS,
];

export function getIntegration(id: string): IntegrationDef | undefined {
  return ALL_INTEGRATIONS.find((i) => i.id === id);
}

export function integrationsByCategory(cat: IntegrationCategory | "all"): IntegrationDef[] {
  if (cat === "all") return ALL_INTEGRATIONS;
  return ALL_INTEGRATIONS.filter((i) => i.category === cat);
}
