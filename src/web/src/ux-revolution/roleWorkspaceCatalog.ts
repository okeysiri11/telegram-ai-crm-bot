/**
 * Sprint 33.1 — Role workspace catalog (Who are you?).
 * Homes map to existing routes — no backend changes.
 */

export type RoleWorkspace = {
  id: string;
  label: string;
  labelEn: string;
  description: string;
  homeRoute: string;
  /** Simple-mode nav ids emphasized for this role */
  simpleNavIds: string[];
  defaultContextModule?: string;
  icon: string;
};

/** Eight enterprise personas asked on first login. */
export const ENTERPRISE_UX_ROLES: RoleWorkspace[] = [
  {
    id: "owner",
    label: "Владелец",
    labelEn: "Owner",
    description: "Платформа, здоровье, безопасность, полный обзор",
    homeRoute: "/owner",
    simpleNavIds: ["dashboard", "ai_assistant", "crm", "finance", "settings"],
    defaultContextModule: "dashboard",
    icon: "OW",
  },
  {
    id: "ceo",
    label: "CEO",
    labelEn: "CEO",
    description: "Executive summary, KPI, риски, рекомендации AI",
    homeRoute: "/dashboard?mode=executive",
    simpleNavIds: ["dashboard", "ai_assistant", "finance", "projects", "notifications"],
    defaultContextModule: "dashboard",
    icon: "CE",
  },
  {
    id: "sales",
    label: "Продажи",
    labelEn: "Sales",
    description: "CRM, сделки, клиенты, коммуникации",
    homeRoute: "/crm",
    simpleNavIds: ["crm", "calendar", "documents", "ai_assistant", "notifications"],
    defaultContextModule: "crm",
    icon: "SA",
  },
  {
    id: "production",
    label: "Производство",
    labelEn: "Production",
    description: "Производственные процессы и проекты",
    homeRoute: "/erp?view=production",
    simpleNavIds: ["projects", "documents", "calendar", "ai_assistant"],
    defaultContextModule: "projects",
    icon: "PR",
  },
  {
    id: "finance",
    label: "Финансы",
    labelEn: "Finance",
    description: "Финансы, аналитика, счета, отчёты",
    homeRoute: "/analytics",
    simpleNavIds: ["finance", "documents", "dashboard", "notifications"],
    defaultContextModule: "finance",
    icon: "FI",
  },
  {
    id: "developer",
    label: "Разработчик",
    labelEn: "Developer",
    description: "Builder Studio, runtime, архитектура",
    homeRoute: "/platform-builder/builder-studio",
    simpleNavIds: ["dashboard", "ai_assistant", "settings", "documents"],
    defaultContextModule: "settings",
    icon: "DV",
  },
  {
    id: "administrator",
    label: "Администратор",
    labelEn: "Administrator",
    description: "Пользователи, настройки, безопасность",
    homeRoute: "/admin",
    simpleNavIds: ["settings", "notifications", "dashboard", "documents"],
    defaultContextModule: "settings",
    icon: "AD",
  },
  {
    id: "ai_engineer",
    label: "AI-инженер",
    labelEn: "AI Engineer",
    description: "AI-агенты, студия, runtime",
    homeRoute: "/ai-agents",
    simpleNavIds: ["ai_assistant", "documents", "projects", "dashboard"],
    defaultContextModule: "ai_assistant",
    icon: "AI",
  },
];

export const ROLE_WORKSPACE_CATALOG = ENTERPRISE_UX_ROLES;

export function roleWorkspaceById(id: string | undefined | null): RoleWorkspace | undefined {
  if (!id) return undefined;
  return ENTERPRISE_UX_ROLES.find((r) => r.id === id);
}

/** Persist selected workspace role (view preference). */
export const ROLE_WORKSPACE_KEY = "ewp_ux_role_workspace_v1";

export function loadRoleWorkspaceId(): string | null {
  try {
    return localStorage.getItem(ROLE_WORKSPACE_KEY);
  } catch {
    return null;
  }
}

export function saveRoleWorkspaceId(id: string): void {
  try {
    localStorage.setItem(ROLE_WORKSPACE_KEY, id);
  } catch {
    /* ignore */
  }
}
