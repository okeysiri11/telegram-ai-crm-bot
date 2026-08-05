/**
 * Unified workspace context helpers — Sprint 32.3.6.
 * Reads existing stores / path; no new Workspace Engine.
 */

import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { BREADCRUMB_LABEL_RU } from "../navigation/enterpriseRuNav";

export type QuickSwitchItem = {
  id: string;
  label: string;
  route: string;
  hint: string;
};

/** Enterprise OS quick switch — existing routes only. */
export const GLOBAL_QUICK_SWITCH: QuickSwitchItem[] = [
  { id: "desktop", label: "Рабочий стол", route: "/desktop", hint: "ОС" },
  { id: "dashboard", label: "Главная", route: "/dashboard", hint: "КЦ" },
  { id: "city", label: "Город", route: "/enterprise-city", hint: "Город" },
  { id: "production", label: "Продакшн", route: "/production-studio", hint: "Прод" },
  { id: "command_center", label: "Командный центр", route: "/command-center", hint: "Кмд" },
  { id: "workspace", label: "Рабочее пространство", route: "/workspace", hint: "РП" },
  { id: "mission_control", label: "Мониторинг", route: "/platform-builder/mission-control", hint: "Мон" },
  { id: "workflows", label: "Процессы", route: "/platform-builder/workflow-center", hint: "ПР" },
  { id: "builder", label: "Конструктор", route: "/platform-builder/builder-studio", hint: "Кнстр" },
  { id: "crm", label: "CRM", route: "/crm", hint: "CRM" },
  { id: "analytics", label: "Аналитика", route: "/analytics", hint: "BI" },
  { id: "documents", label: "Документы", route: "/documents", hint: "Док" },
  { id: "ai_team", label: "AI-Агенты", route: "/ai-agents", hint: "AI" },
  { id: "knowledge", label: "Знания", route: "/knowledge", hint: "БЗ" },
  { id: "owner", label: "Владелец", route: "/owner", hint: "Вл" },
  { id: "settings", label: "Настройки", route: "/settings", hint: "Нстр" },
];

const ECOSYSTEM_LABELS: Record<string, string> = {
  auto: "Авто",
  beauty: "Бьюти",
  cafe: "Кафе",
  agro: "Агро",
  legal: "Юридический",
  crypto: "Bidex",
  drone: "Дроны",
};

const LABEL_OVERRIDES: Record<string, string> = {
  "production-studio": "AI Production Center",
  production: "AI Production Center",
  desktop: "Enterprise Desktop",
  dashboard: "Dashboard",
  "enterprise-city": "Enterprise City",
  city: "Enterprise City",
  "ai-studio": "AI Studio",
  "ai-agents": "AI Agents",
  knowledge: "Knowledge Base",
  documents: "Documents",
  analytics: "Analytics",
  marketplace: "Marketplace",
  automation: "Automation",
  integrations: "Integrations",
  security: "Security",
  projects: "Projects",
  search: "Search",
  "platform-builder": "Platform Builder",
  "mission-control": "Mission Control",
  "ai-team": "AI Team",
  "builder-studio": "Builder Studio",
  builder: "Builder",
  crm: "CRM",
  erp: "ERP",
  docs: "Documents",
  "solution-hub": "Marketplace",
  "digital-twin": "Digital Twin",
  "workflow-center": "Workflow Center",
  "command-center": "Command Center OS",
  framework: "Universal Builder Framework",
  vertical: "Vertical Builder",
  academy: "Builder Academy 2.0",
  "business-ecosystem": "Business Ecosystem",
  strategy: "Strategy Engine",
  "twin-intelligence": "Twin Intelligence",
  "control-tower": "Control Tower",
  finance: "Finance",
  hr: "HR",
  settings: "Settings",
  onboarding: "Onboarding",
  "first-entry": "First Entry",
  demo: "Demo",
  scenario: "Scenario",
  workspace: "Workspace",
  intelligence: "Analytics",
  concierge: "AI Concierge",
  ...ECOSYSTEM_LABELS,
};

export function labelForSegment(segment: string): string {
  const key = segment.toLowerCase();
  if (BREADCRUMB_LABEL_RU[key]) return BREADCRUMB_LABEL_RU[key]!;
  if (LABEL_OVERRIDES[key]) return LABEL_OVERRIDES[key]!;
  try {
    const meta = moduleRegistry.resolve(key);
    if (meta?.title) return meta.title;
  } catch {
    /* ignore */
  }
  return segment.replace(/[-_]/g, " ");
}

export function detectActiveEcosystem(pathname: string): string | null {
  const parts = pathname.split("/").filter(Boolean);
  const wsIdx = parts.indexOf("workspace");
  if (wsIdx >= 0 && parts[wsIdx + 1]) {
    const id = parts[wsIdx + 1]!;
    if (moduleRegistry.ecosystems().includes(id as never)) {
      return ECOSYSTEM_LABELS[id] || id;
    }
  }
  for (const eco of moduleRegistry.ecosystems()) {
    if (pathname.includes(`/${eco}`)) return ECOSYSTEM_LABELS[eco] || eco;
  }
  return null;
}

export function workspaceStatusLabel(activeModules: string[]): string {
  if (!activeModules.length) return "Ожидание";
  return activeModules.length >= 4 ? "В работе" : "Частично";
}
