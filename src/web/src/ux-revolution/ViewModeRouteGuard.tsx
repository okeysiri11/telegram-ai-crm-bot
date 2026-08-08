/**
 * Sprint 41.1 — soft-redirect when View Mode disallows the current route.
 */

import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useViewModeStore, isRouteAllowedForViewMode } from "@/ux-revolution";
import { useI18n } from "@/i18n";

export function ViewModeRouteGuard() {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  const viewMode = useViewModeStore((s) => s.viewMode);
  const t = useI18n((s) => s.t);

  useEffect(() => {
    const full = `${pathname}${search}`;
    if (isRouteAllowedForViewMode(full, viewMode)) return;
    if (pathname.startsWith("/onboarding") || pathname.startsWith("/login") || pathname.startsWith("/auth")) {
      return;
    }
    try {
      sessionStorage.setItem(
        "ewp_view_mode_toast_v1",
        t("viewMode.redirectHidden") || "Раздел скрыт в текущем режиме интерфейса",
      );
    } catch {
      /* ignore */
    }
    navigate("/dashboard", { replace: true });
  }, [pathname, search, viewMode, navigate, t]);

  return null;
}
