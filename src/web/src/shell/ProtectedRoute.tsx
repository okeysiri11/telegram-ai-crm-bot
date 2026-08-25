import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuthStore } from "@/auth/authStore";
import { isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { isClientOnboardingComplete } from "@/multi-role/clientOnboardingStore";
import { demoUserByEmail } from "@/multi-role/demoUsers";
import { loginRedirect, rememberReturnTo } from "@/navigation/safeReturnTo";

/** Paths that require completed onboarding before access. */
const ONBOARDING_GATED = new Set(["/", "/dashboard"]);

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const loc = useLocation();
  if (!user) {
    const from = `${loc.pathname}${loc.search}${loc.hash}`;
    rememberReturnTo(from);
    return <Navigate to={loginRedirect(from)} replace state={{ from }} />;
  }
  if (loc.pathname.startsWith("/onboarding")) return children;

  const isClient =
    user.roleId === "client" || demoUserByEmail(user.email)?.viewMode === "client";

  if (ONBOARDING_GATED.has(loc.pathname)) {
    if (isClient && !isClientOnboardingComplete()) {
      return <Navigate to="/onboarding/client" replace />;
    }
    if (!isClient && !isFirstEntryComplete()) {
      return <Navigate to="/onboarding/first-entry" replace />;
    }
  }
  return children;
}
