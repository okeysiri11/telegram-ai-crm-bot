import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuthStore } from "@/auth/authStore";
import { isFirstEntryComplete } from "@/onboarding/firstEntryStore";

/** Paths that require completed first-entry before access. */
const FIRST_ENTRY_GATED = new Set(["/", "/dashboard"]);

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const loc = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (
    FIRST_ENTRY_GATED.has(loc.pathname) &&
    !isFirstEntryComplete() &&
    !loc.pathname.startsWith("/onboarding")
  ) {
    return <Navigate to="/onboarding/first-entry" replace />;
  }
  return children;
}
