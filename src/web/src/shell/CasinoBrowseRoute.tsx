import { useEffect, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { rememberReturnTo } from "@/navigation/safeReturnTo";

/**
 * Visual casino browse is allowed without login.
 * PLAY actions still go through CasinoGuestModal + loginRedirect(returnTo).
 * Does not change CRM / owner / dashboard ProtectedRoute.
 */
export function CasinoBrowseRoute({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!user) {
      rememberReturnTo(`${loc.pathname}${loc.search}${loc.hash}`);
    }
  }, [loc.hash, loc.pathname, loc.search, user]);

  return children;
}
