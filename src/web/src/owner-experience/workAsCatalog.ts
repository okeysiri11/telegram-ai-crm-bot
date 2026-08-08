/**
 * Sprint 42.9 — «Работаю как» (UI persona → view mode).
 */

import type { ViewModeId } from "@/ux-revolution/viewModeCatalog";

export type WorkAsId =
  | "platform_owner"
  | "ceo"
  | "manager"
  | "operator"
  | "client"
  | "partner"
  | "demo";

export type WorkAsOption = {
  id: WorkAsId;
  label: string;
  viewMode: ViewModeId;
  roleSwitcherId: string;
};

export const WORK_AS_OPTIONS: WorkAsOption[] = [
  {
    id: "platform_owner",
    label: "Владелец платформы",
    viewMode: "platform_owner",
    roleSwitcherId: "owner",
  },
  {
    id: "ceo",
    label: "CEO организации",
    viewMode: "company_admin",
    roleSwitcherId: "administrator",
  },
  {
    id: "manager",
    label: "Менеджер",
    viewMode: "manager",
    roleSwitcherId: "manager",
  },
  {
    id: "operator",
    label: "Оператор",
    viewMode: "manager",
    roleSwitcherId: "manager",
  },
  {
    id: "client",
    label: "Клиент",
    viewMode: "client",
    roleSwitcherId: "client",
  },
  {
    id: "partner",
    label: "Партнёр",
    viewMode: "client",
    roleSwitcherId: "client",
  },
  {
    id: "demo",
    label: "Демо",
    viewMode: "platform_owner",
    roleSwitcherId: "owner",
  },
];

export function workAsFromViewMode(viewMode: ViewModeId): WorkAsId {
  if (viewMode === "platform_owner") return "platform_owner";
  if (viewMode === "company_admin") return "ceo";
  if (viewMode === "manager") return "manager";
  if (viewMode === "client") return "client";
  if (viewMode === "developer") return "demo";
  return "platform_owner";
}

export function workAsLabel(id: WorkAsId): string {
  return WORK_AS_OPTIONS.find((o) => o.id === id)?.label || "Владелец платформы";
}
