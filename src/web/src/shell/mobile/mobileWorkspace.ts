/**
 * Resolve the current workspace label, role, and section nav from existing catalogs.
 * Mobile primary drawer for Agro is operational cabinet B, not domain catalog A.
 */

import { OWNER_RU_NAV } from "@/navigation/enterpriseRuNav";
import { demoUserByEmail } from "@/multi-role/demoUsers";
import { resolveModuleContext } from "@/ux-revolution/moduleContextNav";
import { getVertical, sectionPath, VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";
import { AGRO_OPS_HOME_ID, AGRO_OPS_NAV, agroOpsHref } from "../../../workspace/agro/agroOpsNav";
import type { MobileNavLink } from "./opsCabinetNavStore";

export const PLATFORM_MANAGEMENT_NAV: MobileNavLink[] = [
  { id: "pm_orgs", label: "Организации", href: "/identity/users" },
  { id: "pm_workspace", label: "Workspace", href: "/workspace" },
  { id: "pm_users", label: "Пользователи", href: "/identity/users" },
  { id: "pm_roles", label: "Роли", href: "/settings?tab=interface" },
  { id: "pm_ai", label: "AI Agents", href: "/ai-agents" },
  { id: "pm_integrations", label: "Integrations", href: "/integrations" },
  { id: "pm_health", label: "System Health", href: "/health" },
  { id: "pm_admin", label: "Developer / Admin", href: "/admin" },
  ...OWNER_RU_NAV.filter((item) => !["owner_ai", "owner_admin", "owner_health"].includes(item.id)).map(
    (item) => ({
      id: item.id,
      label: item.label,
      href: item.route,
    }),
  ),
].filter((item, index, all) => all.findIndex((x) => x.href === item.href && x.label === item.label) === index);

export function verticalIdFromPath(pathname: string, fallback = "owner"): string {
  const parts = pathname.split("/").filter(Boolean);
  if ((parts[0] === "workspace" || parts[0] === "vertical") && parts[1]) {
    return parts[1];
  }
  const ctx = resolveModuleContext(pathname, { pro: true });
  if (ctx?.moduleId) return ctx.moduleId;
  return fallback;
}

export function workspaceHomePath(verticalId: string): string {
  if (isOwnerSystemContext(verticalId)) return "/workspace";
  const vertical = getVertical(verticalId);
  return vertical?.legacyRoute || vertical?.route || `/vertical/${verticalId}`;
}

export function isOwnerSystemContext(verticalId: string): boolean {
  return verticalId === "owner" || verticalId === "";
}

export function operationalPanelPath(verticalId: string, lastRoute?: string): string {
  if (lastRoute && isOperationalWorkspaceRoute(lastRoute)) return lastRoute;
  if (!isOwnerSystemContext(verticalId)) return workspaceHomePath(verticalId);
  return "/workspace";
}

export function isOperationalWorkspaceRoute(path: string): boolean {
  return /^\/workspace\/(auto|agro|crypto|legal|beauty|cafe|drone)(\/|\?|$)/.test(path);
}

export const MOBILE_VERTICAL_HUB = [
  { id: "auto", label: "Авто", icon: "🚗", href: "/workspace/auto" },
  { id: "agro", label: "Агро", icon: "🌾", href: "/workspace/agro" },
  { id: "crypto", label: "Crypto", icon: "₿", href: "/workspace/crypto" },
  { id: "legal", label: "Lawyer", icon: "⚖️", href: "/workspace/legal" },
  { id: "beauty", label: "Beauty", icon: "✦", href: "/workspace/beauty" },
  { id: "cafe", label: "Cafe", icon: "☕", href: "/workspace/cafe" },
  { id: "drone", label: "БПЛА", icon: "🛸", href: "/workspace/drone" },
  { id: "crm", label: "CRM", icon: "👤", href: "/crm" },
] as const;

export function resolveMobileHomeWorkspace(storedVertical: string, pathname = ""): string {
  if (!isOwnerSystemContext(storedVertical)) return storedVertical;
  const fromPath = verticalIdFromPath(pathname, "");
  if (fromPath && VERTICAL_WORKSPACES.some((item) => item.id === fromPath) && !isOwnerSystemContext(fromPath)) {
    return fromPath;
  }
  return storedVertical;
}

export function mobileHomeQuickActions(
  _verticalId: string,
): Array<MobileNavLink & { action?: "more" | "create" | "panel" }> {
  return [
    { id: "panel", label: "Открыть панель", href: "__panel__", action: "panel" },
    { id: "ai", label: "Команда AI", href: "/ai-agents" },
    { id: "settings", label: "Настройки", href: "/settings" },
    { id: "more", label: "Ещё", href: "__more__", action: "more" },
  ];
}

export type CreateAction = { id: string; label: string; href: string };

export function createActionsForWorkspace(verticalId: string): CreateAction[] {
  const global: CreateAction[] = [
    { id: "task", label: "Задача", href: "/tasks" },
    { id: "event", label: "Событие", href: "/calendar" },
    { id: "client", label: "Клиент", href: "/crm?view=clients" },
    { id: "document", label: "Документ", href: "/documents" },
    { id: "note", label: "Заметка", href: "/tasks?view=notes" },
  ];
  if (verticalId === "auto") {
    return [
      { id: "vehicle", label: "Автомобиль", href: "/workspace/auto?view=vehicles&action=create" },
      { id: "client", label: "Клиент", href: "/workspace/auto?view=clients" },
      { id: "deal", label: "Сделка", href: "/workspace/auto?view=sales" },
      { id: "pay", label: "Платёж", href: "/workspace/auto?view=expenses" },
      { id: "expense", label: "Расход", href: "/workspace/auto?view=expenses" },
      { id: "ship", label: "Поставка", href: "/workspace/auto?view=logistics" },
      { id: "doc", label: "Документ", href: "/workspace/auto?view=documents" },
      { id: "task", label: "Задача", href: "/workspace/auto?view=tasks" },
    ];
  }
  if (verticalId === "agro") {
    return [
      { id: "cp", label: "Контрагент", href: "/workspace/agro?view=counterparties" },
      { id: "deal", label: "Сделка", href: "/workspace/agro?view=deals" },
      { id: "ship", label: "Поставка", href: "/workspace/agro?view=shipments" },
      { id: "wh", label: "Склад", href: "/workspace/agro?view=warehouses" },
      { id: "doc", label: "Документ", href: "/workspace/agro?view=documents" },
      { id: "task", label: "Задача", href: "/workspace/agro?view=tasks" },
    ];
  }
  return global;
}

export type ImportantItem = { id: string; label: string; href: string };

export function importantTodayFromLive(input: {
  unread: number;
  healthFailed: number;
  unreadTasks?: number;
  unreadAlerts?: number;
}): ImportantItem[] {
  const items: ImportantItem[] = [];
  if ((input.unreadTasks || 0) > 0) {
    items.push({ id: "tasks", label: `Просроченные задачи · ${input.unreadTasks}`, href: "/tasks" });
  }
  if (input.unread > 0) {
    items.push({ id: "notif", label: `Новые уведомления · ${input.unread}`, href: "/notifications" });
  }
  if ((input.unreadAlerts || 0) > 0) {
    items.push({ id: "alerts", label: `Критические события · ${input.unreadAlerts}`, href: "/notifications" });
  }
  if (input.healthFailed > 0) {
    items.push({
      id: "health",
      label: `Системные предупреждения · ${input.healthFailed}`,
      href: "/health",
    });
  }
  return items;
}

export function workspaceContextCopy(
  verticalId: string,
  catalogLabel: string,
): {
  kicker: string;
  title: string;
  roleKicker: string;
  hint?: string;
  systemOwner: boolean;
} {
  if (isOwnerSystemContext(verticalId) || catalogLabel.toLowerCase() === "owner") {
    return {
      kicker: "Режим",
      title: "Владелец системы",
      roleKicker: "Роль",
      hint: "Выберите рабочее пространство",
      systemOwner: true,
    };
  }
  return {
    kicker: "Рабочее пространство",
    title: catalogLabel,
    roleKicker: "Роль",
    systemOwner: false,
  };
}

export function mobileHeaderWorkspaceLabel(verticalId: string, orgLabel?: string): string {
  if (isOwnerSystemContext(verticalId)) return orgLabel || "ADOS";
  return workspaceLabel(verticalId);
}

export function mobileSwitcherItems(): MobileNavLink[] {
  return MOBILE_VERTICAL_HUB.map((item) => ({ id: item.id, label: item.label, href: item.href }));
}

export function demoWorkspaceAvailable(): boolean {
  return Boolean(demoUserByEmail("travel@globefly.demo"));
}

export function isClientDemoSession(email?: string | null): boolean {
  return (email || "").toLowerCase() === "travel@globefly.demo";
}

export function hrefLooksLocal(href: string): boolean {
  return /localhost|127\.0\.0\.1|:5180|:8080/i.test(href);
}

const AUTO_OPS_NAV: Array<{ id: string; label: string }> = [
  { id: "overview", label: "Обзор" },
  { id: "vehicles", label: "Автомобили" },
  { id: "purchases", label: "Закупки" },
  { id: "logistics", label: "Логистика" },
  { id: "customs", label: "Растаможка" },
  { id: "clients", label: "Клиенты" },
  { id: "sales", label: "Продажи" },
  { id: "expenses", label: "Платежи и расходы" },
  { id: "documents", label: "Документы" },
  { id: "tasks", label: "CRM и задачи" },
  { id: "telegram", label: "Telegram" },
  { id: "reports", label: "Отчёты" },
  { id: "analytics", label: "Аналитика" },
  { id: "finance", label: "Финансы" },
  { id: "settings", label: "Настройки" },
];

const BEAUTY_OPS_NAV: Array<{ id: string; label: string }> = [
  { id: "home", label: "Главная" },
  { id: "clients", label: "Клиенты" },
  { id: "services", label: "Услуги" },
  { id: "products", label: "Товары" },
  { id: "bookings", label: "Записи" },
  { id: "calendar", label: "Календарь" },
  { id: "staff", label: "Мастера" },
  { id: "shifts", label: "Смены" },
  { id: "sales", label: "Продажи" },
  { id: "analytics", label: "Аналитика" },
  { id: "marketing", label: "Маркетинг" },
  { id: "warehouse", label: "Склад" },
  { id: "finance", label: "Финансы" },
  { id: "settings", label: "Настройки" },
];

const CAFE_OPS_NAV: Array<{ id: string; label: string }> = [
  { id: "home", label: "Главная" },
  { id: "orders", label: "Заказы" },
  { id: "menu", label: "Меню" },
  { id: "shifts", label: "Смены" },
  { id: "clients", label: "Клиенты" },
  { id: "bookings", label: "Бронирования" },
  { id: "halls", label: "Залы и столы" },
  { id: "warehouse", label: "Склад" },
  { id: "cashier", label: "Касса" },
  { id: "staff", label: "Персонал" },
  { id: "marketing", label: "Маркетинг" },
  { id: "analytics", label: "Аналитика" },
  { id: "settings", label: "Настройки" },
];

const LEGAL_OPS_NAV: Array<{ id: string; label: string }> = [
  { id: "home", label: "Главная" },
  { id: "clients", label: "Клиенты" },
  { id: "cases", label: "Дела" },
  { id: "contracts", label: "Договоры" },
  { id: "documents", label: "Документы" },
  { id: "tasks", label: "Задачи/Сроки" },
  { id: "hearings", label: "Суды/Заседания" },
  { id: "calendar", label: "Календарь" },
  { id: "monitoring", label: "Мониторинг" },
  { id: "inbox", label: "Входящие" },
  { id: "archive", label: "Архив" },
  { id: "ai-analysis", label: "AI-анализ" },
  { id: "ai", label: "AI-юрист" },
  { id: "ai-history", label: "История AI" },
  { id: "activity", label: "Активность" },
  { id: "settings", label: "Настройки" },
];

const CRYPTO_OPS_NAV: Array<{ id: string; label: string }> = [
  { id: "home", label: "Главная" },
  { id: "markets", label: "Рынки" },
  { id: "quotes", label: "Котировки" },
  { id: "charts", label: "Графики" },
  { id: "pairs", label: "Мои инструменты" },
  { id: "analysis", label: "Анализы" },
  { id: "specialists", label: "AI-специалисты" },
  { id: "signals", label: "Сигналы" },
  { id: "news", label: "Новости" },
  { id: "calendar", label: "Календарь" },
  { id: "intel_history", label: "История анализов" },
  { id: "paper", label: "Бумажная торговля" },
  { id: "journal", label: "Журнал" },
  { id: "deals", label: "OTC-сделки" },
  { id: "orders", label: "Ордера" },
  { id: "wallets", label: "Кошельки" },
  { id: "transfers", label: "Переводы" },
  { id: "history", label: "История OTC" },
  { id: "notifications", label: "Уведомления" },
  { id: "settings", label: "Настройки" },
];

function opsLinks(
  verticalId: string,
  items: Array<{ id: string; label: string }>,
  homeId: string,
): MobileNavLink[] {
  return items.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.id === homeId ? `/workspace/${verticalId}` : `/workspace/${verticalId}?view=${item.id}`,
  }));
}

/** Primary mobile workspace navigation — operational cabinets, not domain catalog A. */
export function operationalNavForVertical(verticalId: string): MobileNavLink[] {
  if (verticalId === "agro") {
    return AGRO_OPS_NAV.map((item) => ({
      id: item.id,
      label: item.label,
      href: agroOpsHref(item.id),
    }));
  }
  if (verticalId === "auto") return opsLinks("auto", AUTO_OPS_NAV, "overview");
  if (verticalId === "beauty") return opsLinks("beauty", BEAUTY_OPS_NAV, "home");
  if (verticalId === "cafe") return opsLinks("cafe", CAFE_OPS_NAV, "home");
  if (verticalId === "legal") return opsLinks("legal", LEGAL_OPS_NAV, "home");
  if (verticalId === "crypto") return opsLinks("crypto", CRYPTO_OPS_NAV, "home");
  return [];
}

export function mobileDrawerNav(
  verticalId: string,
  cabinet: { verticalId: string | null; items: MobileNavLink[] },
): MobileNavLink[] {
  if (cabinet.verticalId === verticalId && cabinet.items.length > 0) {
    return cabinet.items;
  }
  const ops = operationalNavForVertical(verticalId);
  if (ops.length) return ops;
  if (isOwnerSystemContext(verticalId)) return [];
  return navFromVertical(verticalId);
}

export function isMobileNavHrefActive(href: string, pathname: string, search: string): boolean {
  const qIndex = href.indexOf("?");
  const path = qIndex >= 0 ? href.slice(0, qIndex) : href;
  const hrefSearch = qIndex >= 0 ? href.slice(qIndex + 1) : "";
  if (path !== pathname) return false;
  const want = new URLSearchParams(hrefSearch).get("view");
  const have = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search).get("view");
  if (!want || want === AGRO_OPS_HOME_ID) return !have || have === "home";
  return have === want;
}

export const MOBILE_EXTRA_ACTIONS: MobileNavLink[] = [
  { id: "docs", label: "Последние документы", href: "/documents" },
  { id: "deals", label: "Последние сделки", href: "/crm?view=deals" },
  { id: "tasks", label: "Задачи", href: "/tasks" },
  { id: "cal", label: "Календарь", href: "/calendar" },
];

export function workspaceLabel(verticalId: string): string {
  return getVertical(verticalId)?.label || verticalId;
}

export function navFromVertical(verticalId: string): MobileNavLink[] {
  const vertical = getVertical(verticalId);
  if (!vertical) return [];
  return vertical.nav.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.href || sectionPath(verticalId, item.id),
  }));
}

export function navFromContext(pathname: string, search = ""): MobileNavLink[] {
  const ctx = resolveModuleContext(`${pathname}${search}`, { pro: true });
  if (!ctx) return [];
  return ctx.items.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.route,
  }));
}

export function sectionTitle(
  pathname: string,
  search: string,
  verticalId: string,
  cabinetItems: MobileNavLink[],
): string | null {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const view = params.get("view");
  const ops = operationalNavForVertical(verticalId);
  if (view) {
    const hit =
      cabinetItems.find((item) => item.id === view) ||
      ops.find((item) => item.id === view) ||
      navFromVertical(verticalId).find((item) => item.id === view);
    if (hit && hit.id !== "home" && hit.id !== "overview") return hit.label;
  }
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "vertical" && parts[2]) {
    const hit = navFromVertical(verticalId).find((item) => item.id === parts[2]);
    if (hit && hit.id !== "home") return hit.label;
  }
  if (parts[0] === "workspace" && parts[2]) {
    const hit =
      cabinetItems.find((item) => item.id === parts[2]) ||
      ops.find((item) => item.id === parts[2]) ||
      navFromVertical(verticalId).find((item) => item.id === parts[2]);
    if (hit && hit.id !== "home" && hit.id !== "overview") return hit.label;
  }
  if (isOperationalWorkspaceRoute(pathname) && !view && !parts[2]) return null;
  const ctx = resolveModuleContext(`${pathname}${search}`, { pro: true });
  if (ctx && pathname !== "/dashboard") return ctx.label;
  return null;
}

export function quickActionsForWorkspace(verticalId: string): MobileNavLink[] {
  const vertical = getVertical(verticalId);
  if (vertical?.quickActions?.length) {
    return vertical.quickActions.slice(0, 5).map((action, index) => ({
      id: `qa_${index}`,
      label: action.label,
      href: action.route,
    }));
  }
  return navFromVertical(verticalId)
    .filter((item) => item.id !== "home")
    .slice(0, 5);
}

export function workspaceSwitcherItems(): MobileNavLink[] {
  return VERTICAL_WORKSPACES.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.legacyRoute || item.route,
  }));
}

export function isDemoAccount(email?: string | null, tenantId?: string | null): boolean {
  const mail = (email || "").toLowerCase();
  const tenant = (tenantId || "").toLowerCase();
  return (
    mail.includes("@demo.") ||
    mail.endsWith("@ados.demo") ||
    tenant.includes("demo") ||
    tenant === "ados"
  );
}
