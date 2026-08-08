/**
 * Sprint 41.1 — Interface View Mode (UI only; not security roles).
 */

export type ViewModeId =
  | "client"
  | "manager"
  | "company_admin"
  | "platform_owner"
  | "developer";

export type ViewModeOption = {
  id: ViewModeId;
  labelRu: string;
  labelEn: string;
  descriptionRu: string;
};

/** Canonical View Modes — order used in header selector. */
export const VIEW_MODE_OPTIONS: ViewModeOption[] = [
  {
    id: "client",
    labelRu: "Клиент",
    labelEn: "Client",
    descriptionRu: "Рабочие модули клиента без инструментов платформы",
  },
  {
    id: "manager",
    labelRu: "Менеджер",
    labelEn: "Manager",
    descriptionRu: "CRM, задачи и отчёты без конструкторов",
  },
  {
    id: "company_admin",
    labelRu: "Администратор компании",
    labelEn: "Company Administrator",
    descriptionRu: "Администрирование компании без runtime и builders",
  },
  {
    id: "platform_owner",
    labelRu: "Владелец платформы",
    labelEn: "Platform Owner",
    descriptionRu: "Полный интерфейс платформы",
  },
  {
    id: "developer",
    labelRu: "Разработчик",
    labelEn: "Developer",
    descriptionRu: "Диагностика, runtime, builders и инфраструктура",
  },
];

/** Route prefixes / exact paths allowed per view mode (Client = strict allowlist). */
const CLIENT_ROUTES = [
  "/dashboard",
  "/desktop",
  "/crm",
  "/leads",
  "/clients",
  "/deals",
  "/companies",
  "/documents",
  "/tasks",
  "/calendar",
  "/ai-agents",
  "/analytics",
  "/reports",
  "/knowledge",
  "/support",
  "/settings",
  "/identity/profile",
  "/profile",
  "/notifications",
  "/search",
  "/onboarding",
  "/auth/logout",
  "/login",
  "/marketplace",
  "/workspace/legal",
] as const;

const MANAGER_EXTRA = [
  "/projects",
  "/erp",
  "/marketplace",
  "/knowledge",
  "/dashboards",
  "/workspace/crypto",
  "/workspace/drone",
  "/workspace/auto",
  "/workspace/agro",
  "/workspace/cafe",
  "/workspace/legal",
] as const;

const COMPANY_ADMIN_EXTRA = [
  "/admin",
  "/identity",
  "/health",
] as const;

/** Routes always hidden from Client / Manager (builders & infra). */
export const DEVELOPER_ONLY_ROUTE_MARKERS = [
  "/platform-builder",
  "/command-runtime",
  "/kernel",
  "/owner",
  "/city",
  "/ai-studio",
  "/production-studio",
  "/workflow",
  "/command-center",
  "/god-mode",
  "/runtime",
] as const;

function matchesAny(path: string, markers: readonly string[]): boolean {
  const p = path.split("?")[0] || path;
  return markers.some((m) => p === m || p.startsWith(`${m}/`) || p.startsWith(m));
}

function matchesAllowlist(path: string, allow: readonly string[]): boolean {
  const full = path.toLowerCase();
  const base = (full.split("?")[0] || full).replace(/\/$/, "") || "/";
  return allow.some((a) => {
    const ab = a.toLowerCase();
    return full === ab || base === ab || base.startsWith(`${ab}/`) || full.startsWith(`${ab}?`);
  });
}

export function isRouteAllowedForViewMode(route: string, mode: ViewModeId): boolean {
  const path = route.startsWith("/") ? route : `/${route}`;
  if (mode === "platform_owner" || mode === "developer") return true;

  if (mode === "client") {
    if (matchesAny(path, DEVELOPER_ONLY_ROUTE_MARKERS)) return false;
    return matchesAllowlist(path, CLIENT_ROUTES);
  }

  if (mode === "manager") {
    if (matchesAny(path, DEVELOPER_ONLY_ROUTE_MARKERS)) return false;
    return matchesAllowlist(path, [...CLIENT_ROUTES, ...MANAGER_EXTRA]);
  }

  // company_admin
  if (matchesAny(path, ["/platform-builder", "/command-runtime", "/kernel", "/god-mode", "/runtime", "/ai-studio", "/production-studio"])) {
    return false;
  }
  return matchesAllowlist(path, [...CLIENT_ROUTES, ...MANAGER_EXTRA, ...COMPANY_ADMIN_EXTRA, "/city"]);
}

export function viewModeLabel(mode: ViewModeId, locale: "ru" | "en" | "uk" = "ru"): string {
  const opt = VIEW_MODE_OPTIONS.find((o) => o.id === mode);
  if (!opt) return mode;
  return locale === "en" ? opt.labelEn : opt.labelRu;
}

/** Map legacy role-switcher ids → view mode for migration. */
export function legacyRoleToViewMode(roleId: string | null | undefined): ViewModeId | null {
  if (!roleId) return null;
  if (roleId === "owner" || roleId === "platform_owner") return "platform_owner";
  if (roleId === "administrator" || roleId === "admin") return "company_admin";
  if (roleId === "manager" || roleId === "employee" || roleId === "dealer" || roleId === "partner") {
    return "manager";
  }
  if (roleId === "client" || roleId === "viewer") return "client";
  if (roleId === "developer") return "developer";
  return null;
}
