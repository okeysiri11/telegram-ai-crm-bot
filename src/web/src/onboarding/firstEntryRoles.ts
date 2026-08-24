/**
 * First-entry role catalog — Sprint 32.3.1 + 33.1 Enterprise UX personas.
 * Extensible: append via registerFirstEntryRole() without architecture changes.
 */

import { ENTERPRISE_UX_ROLES } from "@/ux-revolution/roleWorkspaceCatalog";

export type FirstEntryRole = {
  id: string;
  label: string;
  description: string;
  /** Maps to existing business ecosystem / workspace module when applicable */
  ecosystemHint?: string;
  workspaceRoute?: string;
  icon: string;
};

const ENTERPRISE_PERSONAS: FirstEntryRole[] = ENTERPRISE_UX_ROLES.map((r) => ({
  id: r.id,
  label: r.label,
  description: r.description,
  icon: r.icon,
  ecosystemHint: "platform",
  workspaceRoute: r.homeRoute,
}));

const ROLES: FirstEntryRole[] = [
  ...ENTERPRISE_PERSONAS,
  {
    id: "business_owner",
    label: "Владелец (legacy)",
    description: "Полный доступ · панель владельца · все модули",
    icon: "OW",
    ecosystemHint: "platform",
    workspaceRoute: "/owner",
  },
  {
    id: "manager",
    label: "Менеджер",
    description: "Команда · проекты · CRM · операционные KPI",
    icon: "MG",
    ecosystemHint: "platform",
    workspaceRoute: "/dashboards/manager",
  },
  {
    id: "employee",
    label: "Сотрудник",
    description: "Задачи · календарь · документы · уведомления",
    icon: "EM",
    ecosystemHint: "platform",
    workspaceRoute: "/dashboards/employee",
  },
  {
    id: "client",
    label: "Клиент",
    description: "Покупатель или заказчик услуг",
    icon: "CL",
    workspaceRoute: "/dashboards/client",
  },
  {
    id: "executive",
    label: "Executive / Руководитель",
    description: "KPI, health, AI и критические события на одном экране",
    icon: "EX",
    ecosystemHint: "platform",
    workspaceRoute: "/dashboard?mode=executive",
  },
  {
    id: "beauty_salon",
    label: "Салон красоты",
    description: "Beauty ecosystem — записи, клиенты, команда",
    icon: "BE",
    ecosystemHint: "beauty",
    workspaceRoute: "/workspace/beauty",
  },
  {
    id: "auto_service",
    label: "Автосервис",
    description: "Automotive ecosystem — лиды, склад, дилер",
    icon: "AU",
    ecosystemHint: "auto",
    workspaceRoute: "/workspace/auto",
  },
  {
    id: "legal_firm",
    label: "Юридическая компания",
    description: "Legal ecosystem — дела, документы, compliance",
    icon: "LE",
    ecosystemHint: "legal",
    workspaceRoute: "/workspace/legal",
  },
  {
    id: "agro_business",
    label: "Агробизнес",
    description: "Урожай, логистика и экспорт",
    icon: "AG",
    ecosystemHint: "agro",
    workspaceRoute: "/workspace/agro",
  },
  {
    id: "trader",
    label: "Трейдер",
    description: "Торговые и финансовые операции",
    icon: "TR",
    ecosystemHint: "crypto",
    workspaceRoute: "/workspace/crypto",
  },
  {
    id: "drone",
    label: "Drone",
    description: "Drone ecosystem — флот, миссии, производство",
    icon: "DR",
    ecosystemHint: "drone",
    workspaceRoute: "/workspace/drone",
  },
  {
    id: "bidex",
    label: "Bidex",
    description: "Bidex — KYC, кошельки, OTC, settlement",
    icon: "BX",
    ecosystemHint: "crypto",
    workspaceRoute: "/workspace/crypto",
  },
  {
    id: "manufacturing",
    label: "Производство (vertical)",
    description: "Производственные и складские процессы",
    icon: "MF",
    ecosystemHint: "drone",
    workspaceRoute: "/workspace/drone",
  },
  {
    id: "cafe",
    label: "Cafe / F&B",
    description: "Cafe ecosystem — меню, кухня, бронирования",
    icon: "CA",
    ecosystemHint: "cafe",
    workspaceRoute: "/workspace/cafe",
  },
];

/** Mutable catalog — callers may register additional roles at runtime. */
export const firstEntryRoleCatalog = {
  list(): FirstEntryRole[] {
    return [...ROLES];
  },
  /** Sprint 33.1 — primary enterprise personas for “Who are you?” */
  enterpriseList(): FirstEntryRole[] {
    return [...ENTERPRISE_PERSONAS];
  },
  get(id: string): FirstEntryRole | undefined {
    return ROLES.find((r) => r.id === id);
  },
  register(role: FirstEntryRole): void {
    const idx = ROLES.findIndex((r) => r.id === role.id);
    if (idx >= 0) ROLES[idx] = role;
    else ROLES.push(role);
  },
};

export function registerFirstEntryRole(role: FirstEntryRole): void {
  firstEntryRoleCatalog.register(role);
}

export const FIRST_ENTRY_STEPS = [
  { id: "welcome", label: "Welcome" },
  { id: "role", label: "Role" },
  { id: "workspace", label: "Workspace" },
  { id: "ready", label: "Ready" },
  { id: "ai_team", label: "AI Team" },
  { id: "concierge", label: "Concierge" },
  { id: "dashboard", label: "Dashboard" },
] as const;

export type FirstEntryStepId = (typeof FIRST_ENTRY_STEPS)[number]["id"];

export const TEAM_SIZE_OPTIONS = [
  { id: "1", label: "Только я" },
  { id: "2-10", label: "2–10" },
  { id: "11-50", label: "11–50" },
  { id: "51-200", label: "51–200" },
  { id: "200+", label: "200+" },
] as const;

export const INDUSTRY_OPTIONS = [
  { id: "beauty", label: "Beauty" },
  { id: "automotive", label: "Automotive" },
  { id: "legal", label: "Legal" },
  { id: "agriculture", label: "Агро" },
  { id: "cafe", label: "Cafe / F&B" },
  { id: "crypto", label: "Bidex / Crypto" },
  { id: "drone", label: "Drone" },
  { id: "manufacturing", label: "Manufacturing" },
  { id: "other", label: "Other" },
] as const;
