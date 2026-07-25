import type { ReactNode } from "react";
import { createContext, useContext, useEffect } from "react";
import { searchIndex } from "../managers/searchIndex";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";

type NavUiState = {
  openPalette: () => void;
  closePalette: () => void;
  paletteOpen: boolean;
};

const Ctx = createContext<NavUiState | null>(null);

export function useNavigationUi() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useNavigationUi requires NavigationProvider");
  return ctx;
}

/** Bridges navigation chrome to Enterprise Command Center palette (Sprint 26.6). */
export function NavigationProvider({ children }: { children: ReactNode }) {
  const cc = useCommandCenterUi();

  useEffect(() => {
    const id = window.setInterval(() => searchIndex.refresh(), 60_000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <Ctx.Provider
      value={{
        paletteOpen: cc.paletteOpen,
        openPalette: cc.openPalette,
        closePalette: cc.close,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
