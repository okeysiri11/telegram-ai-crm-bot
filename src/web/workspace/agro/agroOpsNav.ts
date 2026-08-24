/**
 * Operational Agro workspace navigation (cabinet B).
 * AGRO 2.6: Поля / Культуры / Посевы / Техника / Работы / Урожай are real ops modules.
 * Domain catalog A leftovers (Товары, Полив, ИИ-помощник) stay excluded from the drawer.
 */

export type AgroOpsNavItem = { id: string; label: string };

export const AGRO_OPS_HOME_ID = "home";

export const AGRO_OPS_NAV: AgroOpsNavItem[] = [
  { id: "home", label: "Главная" },
  { id: "command", label: "Командный центр" },
  { id: "report", label: "Сводка" },
  { id: "fields", label: "Поля" },
  { id: "crops", label: "Культуры" },
  { id: "sowing", label: "Посевы" },
  { id: "machinery", label: "Техника" },
  { id: "works", label: "Работы" },
  { id: "harvest", label: "Урожай" },
  { id: "operations", label: "Операции" },
  { id: "counterparties", label: "Контрагенты" },
  { id: "deals", label: "Сделки" },
  { id: "contracts", label: "Договоры" },
  { id: "documents", label: "Документы" },
  { id: "calculations", label: "Расчёты" },
  { id: "accounting", label: "Бухгалтерия" },
  { id: "shipments", label: "Поставки" },
  { id: "warehouses", label: "Склады" },
  { id: "weather", label: "Погода" },
  { id: "markets", label: "Цены и рынки" },
  { id: "logistics", label: "Логистика" },
  { id: "intel", label: "Агро-разведка" },
  { id: "analytics", label: "Аналитика" },
  { id: "calendar", label: "Календарь" },
  { id: "tasks", label: "Задачи" },
  { id: "notifications", label: "Уведомления" },
  { id: "settings", label: "Настройки" },
];

/** Domain catalog A labels that must not appear as duplicate drawer entries. */
export const AGRO_DOMAIN_MENU_LABELS = [
  "Товары",
  "Полив",
  "ИИ-помощник",
] as const;

export function agroOpsHref(id: string): string {
  if (!id || id === AGRO_OPS_HOME_ID || id === "command") return id === "command" ? "/workspace/agro?view=command" : "/workspace/agro";
  return `/workspace/agro?view=${encodeURIComponent(id)}`;
}
