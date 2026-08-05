import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { searchIndex } from "../managers/searchIndex";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";
import { QuickSwitcher } from "./QuickSwitcher";
import { navigationAnalytics } from "../managers/navigationAnalytics";

type NavUiState = {
  openPalette: () => void;
  closePalette: () => void;
  paletteOpen: boolean;
  openQuickSwitcher: () => void;
  quickSwitcherOpen: boolean;
};

const Ctx = createContext<NavUiState | null>(null);

export function useNavigationUi() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useNavigationUi requires NavigationProvider");
  return ctx;
}

/** Bridges navigation chrome to Command Center + Quick Switcher (Sprint 26.7 / 33.2.1). */
export function NavigationProvider({ children }: { children: ReactNode }) {
  const cc = useCommandCenterUi();
  const [quickOpen, setQuickOpen] = useState(false);
  const openQuickSwitcher = useCallback(() => setQuickOpen(true), []);

  useEffect(() => {
    const id = window.setInterval(() => {
      if (typeof document !== "undefined" && document.hidden) return;
      searchIndex.refresh();
    }, 60_000);
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "Tab") {
        e.preventDefault();
        setQuickOpen(true);
      }
      if (e.key === "Escape") {
        setQuickOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    navigationAnalytics.trackPath(window.location.pathname);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  const value = useMemo(
    () => ({
      paletteOpen: cc.paletteOpen,
      openPalette: cc.openPalette,
      closePalette: cc.close,
      quickSwitcherOpen: quickOpen,
      openQuickSwitcher,
    }),
    [cc.paletteOpen, cc.openPalette, cc.close, quickOpen, openQuickSwitcher],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <QuickSwitcher open={quickOpen} onClose={() => setQuickOpen(false)} />
    </Ctx.Provider>
  );
}
