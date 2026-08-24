import { useEffect } from "react";
import { useMobileChromeStore } from "./mobileChromeStore";

const OVERLAY_STATE = { adosMobileOverlay: true } as const;

export function anyMobileOverlayOpen(): boolean {
  const s = useMobileChromeStore.getState();
  return s.drawerOpen || s.moreOpen || s.createOpen || s.searchOpen || s.switcherOpen || s.favoritesOpen;
}

export function closeMobileOverlay(): void {
  if (typeof window !== "undefined" && window.history.state?.adosMobileOverlay) {
    window.history.back();
    return;
  }
  useMobileChromeStore.getState().closeAll();
}

export function navigateFromMobileOverlay(navigate: (to: string, opts?: { replace?: boolean }) => void, to: string): void {
  const overlay = typeof window !== "undefined" && Boolean(window.history.state?.adosMobileOverlay);
  useMobileChromeStore.getState().closeAll();
  navigate(to, { replace: overlay });
}

/** Android back closes the open drawer/sheet first instead of leaving the workspace. */
export function useMobileOverlayHistory(): void {
  const open = useMobileChromeStore(
    (s) => s.drawerOpen || s.moreOpen || s.createOpen || s.searchOpen || s.switcherOpen || s.favoritesOpen,
  );

  useEffect(() => {
    if (!open) return undefined;
    window.history.pushState(OVERLAY_STATE, "");
    const onPop = () => {
      useMobileChromeStore.getState().closeAll();
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [open]);
}
