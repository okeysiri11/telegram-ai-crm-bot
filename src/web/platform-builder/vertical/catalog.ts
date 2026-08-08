export type HelpBits = {
  shortDescription: string;
  purpose: string;
  benefits: string;
  example: string;
  businessValue: string;
  typicalUseCases?: string;
  tooltip: string;
  moreInformation: string;
};

function help(
  purpose: string,
  benefits: string,
  example: string,
  what = "",
  useCases = "",
): HelpBits {
  return {
    shortDescription: what || purpose,
    purpose,
    benefits,
    example,
    businessValue: benefits,
    typicalUseCases: useCases || example,
    tooltip: purpose,
    moreInformation: `${purpose} ${benefits}`,
  };
}

export const VERTICAL_WIZARD_STEPS = [
  "Vertical Information",
  "Select Industry",
  "Module Selection",
  "AI Конфигурация",
  "AI Concierge",
  "Панель управления",
  "Workspace",
  "Live Организация Предпросмотр",
  "Итоги",
  "Создать",
] as const;

export const BUSINESS_SIZES = [
  { id: "solo", name: "Solo" },
  { id: "small", name: "Small" },
  { id: "medium", name: "Medium" },
  { id: "enterprise", name: "Enterprise" },
];

export const BRAND_COLORS = [
  { id: "ocean", name: "Ocean", hex: "#1B6CA8" },
  { id: "forest", name: "Forest", hex: "#2F6B4F" },
  { id: "ember", name: "Ember", hex: "#C45C26" },
  { id: "slate", name: "Slate", hex: "#4A5568" },
  { id: "violet", name: "Violet", hex: "#5B4B8A" },
];

export const INDUSTRIES = [
  { id: "medical", name: "Medical", help: help("Healthcare clinics and medical practices.", "Faster patient coordination and clearer operational visibility.", "Пример: dental clinic with visit CRM and Medical AI.", "Medical vertical", "Patient intake, treatment plans, follow-ups.") },
  { id: "beauty", name: "Beauty", help: help("Salons, spas, and beauty studios.", "Better booking rhythm and client retention.", "Пример: salon with appointment CRM.", "Beauty vertical", "Appointments, memberships, product sales.") },
  { id: "construction", name: "Construction", help: help("Builders and project contractors.", "Clearer project tracking and document control.", "Пример: renovation firm with project ERP.", "Construction vertical", "Sites, permits, materials, crews.") },
  { id: "manufacturing", name: "Manufacturing", help: help("Production and factory operations.", "Tighter inventory and production awareness.", "Пример: parts plant with warehouse + ERP.", "Manufacturing vertical", "BOMs, production runs, quality checks.") },
  { id: "automotive", name: "Automotive", help: help("Dealerships, service, and auto marketplace.", "Stronger inventory and customer lifecycle.", "Пример: dealer with vehicle CRM.", "Automotive vertical", "Sales pipeline, service bookings, parts.") },
  { id: "agriculture", name: "Agriculture", help: help("Farms and agribusiness operations.", "Seasonal planning with clearer field insights.", "Пример: farm with crop analytics.", "Agriculture vertical", "Fields, harvest, suppliers, logistics.") },
  { id: "education", name: "Education", help: help("Schools, academies, and training centers.", "Smoother enrollment and learning operations.", "Пример: academy with student CRM.", "Education vertical", "Enrollment, classes, tutors, billing.") },
  { id: "retail", name: "Retail", help: help("Stores and omnichannel retail.", "Better stock visibility and customer journeys.", "Пример: boutique with marketplace + CRM.", "Retail vertical", "Catalog, orders, loyalty, returns.") },
  { id: "finance", name: "Finance", help: help("Financial services and advisory firms.", "Clearer client portfolios and compliance rhythm.", "Пример: advisory desk with Finance AI.", "Finance vertical", "Clients, portfolios, reports, reminders.") },
  { id: "legal", name: "Legal", help: help("Law firms and legal practices.", "Faster matter tracking and document readiness.", "Пример: firm with Legal AI and knowledge base.", "Legal vertical", "Matters, contracts, deadlines, clients.") },
  { id: "crypto", name: "Crypto", help: help("Digital asset and crypto operations.", "Faster market awareness with specialist AI.", "Пример: trading desk with Crypto AI.", "Crypto vertical", "Watchlists, alerts, treasury, reporting.") },
  { id: "hospitality", name: "Hospitality", help: help("Hotels and guest experience businesses.", "Smoother bookings and guest concierge support.", "Пример: boutique hotel with Concierge + CRM.", "Hospitality vertical", "Reservations, rooms, guests, upsells.") },
  { id: "logistics", name: "Logistics", help: help("Freight, fleet, and delivery networks.", "Clearer routing and warehouse coordination.", "Пример: courier with logistics ERP.", "Logistics vertical", "Shipments, routes, warehouses, partners.") },
  { id: "real_estate", name: "Real Estate", help: help("Agencies and property operations.", "Faster listings and client matching.", "Пример: agency with listing CRM.", "Real Estate vertical", "Listings, viewings, contracts, owners.") },
  { id: "port", name: "Port", help: help("Port and terminal operations.", "Better berth and cargo coordination.", "Пример: terminal with Port Director AI.", "Port vertical", "Berths, cargo, vessels, customs.") },
  { id: "marketplace", name: "Маркетплейс", help: help("Multi-vendor marketplace platforms.", "Stronger seller and listing operations.", "Пример: auto marketplace with seller CRM.", "Маркетплейс vertical", "Listings, vendors, orders, payouts.") },
  { id: "restaurant", name: "Restaurant", help: help("Restaurants and food service.", "Smoother reservations and kitchen ops.", "Пример: restaurant with booking CRM.", "Restaurant vertical", "Menus, tables, orders, suppliers.") },
  { id: "custom", name: "Custom", help: help("Define a vertical unique to your organization.", "Fits any industry blueprint.", "Пример: niche clinic network.", "Custom vertical", "Any modules and AI mix you choose.") },
];

export const MODULES = [
  { id: "crm", name: "CRM", help: help("Customer and pipeline management.", "Stronger relationships and follow-ups.", "Пример: track clinic patients.") },
  { id: "erp", name: "ERP", help: help("Core business operations.", "One operational backbone.", "Пример: manage production resources.") },
  { id: "finance", name: "Finance", help: help("Money, invoices, and cash flow.", "Clearer financial control.", "Пример: weekly cash overview.") },
  { id: "warehouse", name: "Warehouse", help: help("Inventory and stock locations.", "Fewer stock surprises.", "Пример: parts warehouse levels.") },
  { id: "documents", name: "Documents", help: help("Files and document folders.", "Faster document access.", "Пример: contracts library.") },
  { id: "analytics", name: "Аналитика", help: help("Metrics and business trends.", "Better decision visibility.", "Пример: conversion dashboard.") },
  { id: "knowledge_base", name: "База знаний Base", help: help("Approved company knowledge.", "Consistent answers for teams and AI.", "Пример: refund policy wiki.") },
  { id: "automation", name: "Автоматизация", help: help("Repeatable automated actions.", "Less manual busywork.", "Пример: welcome sequence.") },
  { id: "marketplace", name: "Маркетплейс", help: help("Listings and marketplace ops.", "Growth through selling channels.", "Пример: published listings board.") },
  { id: "telegram", name: "Telegram", help: help("Telegram messaging channel.", "Reach customers where they chat.", "Пример: booking bot.") },
  { id: "mobile", name: "Mobile", help: help("Mobile experience layer.", "Work on the go.", "Пример: field staff app.") },
  { id: "website", name: "Website", help: help("Public web presence.", "Attract and convert visitors.", "Пример: booking landing page.") },
  { id: "api", name: "API", help: help("Integration endpoints.", "Connect external systems.", "Пример: partner sync API.") },
  { id: "calendar", name: "Calendar", help: help("Schedules and meetings.", "Reliable planning.", "Пример: clinic appointment calendar.") },
  { id: "notifications", name: "Notifications", help: help("Alerts and reminders.", "Important news arrives on time.", "Пример: renewal reminder.") },
  { id: "workflows", name: "Сценарии", help: help("Потоки бизнес-процессов.", "Согласованные передачи.", "Пример: сценарий онбординга.") },
];

export const AI_MODES = [
  { id: "connect_existing", name: "Connect existing AI Team", help: help("Link specialists already in Центр команды AI / AI Registry.", "Reuse trained specialists immediately.", "Пример: attach Medical + Finance AI to a clinic vertical.") },
  { id: "launch_ai_builder", name: "Launch AI Builder", help: help("Open AI Builder to create new specialists for this vertical.", "Build the exact AI team your industry needs.", "Пример: create Construction AI with permit knowledge.") },
];

export const CONCIERGE_MODES = [
  { id: "attach_existing", name: "Attach Concierge", help: help("Attach the organization’s existing Concierge.", "Keep one central intelligence linked to the vertical.", "Пример: attach Nova Concierge to Medical Vertical.") },
  { id: "create_new", name: "Создать New Concierge", help: help("Prepare a new Concierge via Конструктор AI Консьержа.", "Stand up executive assistance with the vertical.", "Пример: launch Конструктор AI Консьержа for a new org.") },
];

export const DASHBOARD_WIDGETS = [
  { id: "kpi_overview", name: "KPI Обзор" },
  { id: "pipeline", name: "Pipeline" },
  { id: "revenue", name: "Revenue" },
  { id: "ai_team_status", name: "AI Team Статус" },
  { id: "concierge_brief", name: "Concierge Brief" },
  { id: "tasks", name: "Tasks" },
  { id: "calendar", name: "Calendar" },
  { id: "alerts", name: "Alerts" },
  { id: "knowledge_highlights", name: "База знаний Highlights" },
  { id: "organization_map", name: "Карта организации" },
];

export const DEFAULT_DEPARTMENTS = ["Leadership", "Operations", "Sales", "Finance", "Support"];

export const AI_EXPLANATION =
  "Every AI Specialist has independent memory and specialization. Multiple AI Specialists work together as one intelligent organization.";

export type VerticalDraft = {
  name: string;
  description: string;
  industry: string | null;
  industryCustom: string;
  businessSize: string;
  logo: string;
  brandColor: string;
  modules: string[];
  aiMode: string;
  conciergeMode: string;
  dashboardWidgets: string[];
  workspaceName: string;
  departments: string[];
  menus: string[];
  navigation: string[];
  ownerName: string;
};

export function emptyDraft(): VerticalDraft {
  return {
    name: "",
    description: "",
    industry: null,
    industryCustom: "",
    businessSize: "medium",
    logo: "logo_mark",
    brandColor: "ocean",
    modules: ["crm", "knowledge_base", "analytics", "workflows"],
    aiMode: "connect_existing",
    conciergeMode: "attach_existing",
    dashboardWidgets: ["kpi_overview", "ai_team_status", "concierge_brief", "organization_map"],
    workspaceName: "",
    departments: [...DEFAULT_DEPARTMENTS],
    menus: ["Главная", "CRM", "AI Team", "База знаний", "Настройки"],
    navigation: ["dashboard", "workspace", "ai_team", "concierge"],
    ownerName: "Owner",
  };
}
