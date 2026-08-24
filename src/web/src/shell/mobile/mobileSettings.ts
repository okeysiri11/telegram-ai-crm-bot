/**
 * Mobile settings catalog. Visibility is derived from the same auth roles
 * the APIs already enforce — UI hiding is not a substitute for server RBAC.
 */

import { resolveCabinetCaps } from "../../../workspace/business-ops/cabinetCapabilities";
import { isPlatformOwner } from "../../../platform-builder/managers/platformOwner";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";

export type MobileSettingsItem = {
  id: string;
  label: string;
  href: string;
  ownerOnly?: boolean;
  auto?: boolean;
  agro?: boolean;
};

export const MOBILE_SETTINGS_CATALOG: MobileSettingsItem[] = [
  { id: "profile", label: "Профиль", href: "/settings?tab=profile" },
  { id: "organization", label: "Организация", href: "/settings?tab=organization" },
  { id: "workspaces", label: "Рабочие пространства", href: "/workspace" },
  { id: "users", label: "Пользователи и роли", href: "/identity/users", ownerOnly: true },
  { id: "telegram", label: "Telegram", href: "/settings?tab=telegram" },
  { id: "notifications", label: "Уведомления", href: "/settings?tab=notifications" },
  { id: "security", label: "Безопасность", href: "/settings?tab=security" },
  { id: "ai", label: "AI", href: "/ai-agents" },
  { id: "auto", label: "AUTO", href: "/workspace/auto?view=settings", auto: true },
  { id: "agro", label: "AGRO", href: "/workspace/agro?view=settings", agro: true },
  { id: "sources", label: "Источники данных", href: "/integrations", ownerOnly: true },
];

export function visibleMobileSettings(): MobileSettingsItem[] {
  const owner = isPlatformOwner() || useRoleSwitcher.getState().isOwnerView();
  const auto = resolveCabinetCaps("auto");
  const agro = resolveCabinetCaps("agro");
  return MOBILE_SETTINGS_CATALOG.filter((item) => {
    if (item.ownerOnly && !owner && !auto.canConfigure && !agro.canConfigure) return false;
    if (item.auto && auto.isCustomer) return false;
    if (item.agro && agro.isCustomer) return false;
    if (item.id === "ai" && auto.isCustomer && agro.isCustomer && !owner) return false;
    return true;
  });
}
