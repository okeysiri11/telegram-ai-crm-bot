/**
 * Sprint 49.1 — role-aware cabinet capabilities.
 * Uses auth permissions/roles first; view-as role switcher is navigation context only.
 */

import { accessMiddleware, type AccessContext } from "../../auth/managers/enterpriseAccess";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";

export type CabinetCaps = {
  canCreate: boolean;
  canOperate: boolean;
  canConfigure: boolean;
  canSeeAnalytics: boolean;
  canSeeFinance: boolean;
  isCustomer: boolean;
  roleLabel: string;
};

function buildCtx(): AccessContext {
  const user = useAuthStore.getState().user;
  const roles = [
    ...(user?.roles || []),
    user?.roleId || "",
    useRoleSwitcher.getState().activeRoleId,
  ].filter(Boolean);
  return {
    roles,
    permissions: user?.permissions || [],
    tenantId: (user as { tenantId?: string } | undefined)?.tenantId,
  };
}

export function resolveCabinetCaps(vertical: "beauty" | "cafe" | "crypto" | "legal" | "agro" | "auto"): CabinetCaps {
  const ctx = buildCtx();
  const viewAs = useRoleSwitcher.getState().activeRoleId.toLowerCase();
  const isCustomer =
    viewAs.includes("client") ||
    viewAs === "customer" ||
    ctx.roles.some((r) => /client|customer/i.test(r));

  if (isCustomer) {
    return {
      canCreate: false,
      canOperate: false,
      canConfigure: false,
      canSeeAnalytics: false,
      canSeeFinance: false,
      isCustomer: true,
      roleLabel: "Клиент",
    };
  }

  const canConfigure =
    accessMiddleware(ctx, "admin") ||
    accessMiddleware(ctx, "settings") ||
    ctx.roles.some((r) => /owner|admin|manager|partner|platform_owner/i.test(r));

  const canSeeAnalytics =
    canConfigure || accessMiddleware(ctx, "analytics") || ctx.roles.some((r) => /manager|owner|trader|lawyer|partner/i.test(r));

  const canOperate = !isCustomer;
  const observerOnly = /observer|viewer|наблюдатель/i.test(viewAs);
  const canCreate =
    canOperate &&
    !observerOnly &&
    (canConfigure || !/cashier|viewer/i.test(viewAs) || vertical === "cafe" || vertical === "legal" || vertical === "agro");

  // Waiter/master/operator: operate yes, finance/settings limited
  const staffOnly = /master|waiter|bartender|chef|cashier|operator|employee|paralegal|помощник/i.test(viewAs);
  return {
    canCreate,
    canOperate: canOperate && !observerOnly,
    canConfigure: canConfigure && !staffOnly,
    canSeeAnalytics: canSeeAnalytics && !(staffOnly && !/manager|partner|lawyer/i.test(viewAs)),
    canSeeFinance: canConfigure || ((vertical === "agro" || vertical === "auto") && /accountant|бухгалтер|director|директор/i.test(viewAs)),
    isCustomer: false,
    roleLabel: useRoleSwitcher.getState().activeOption()?.label || viewAs || "Сотрудник",
  };
}
