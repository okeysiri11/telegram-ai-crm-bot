import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { CommandPalette } from "./CommandPalette";
import { searchIndex } from "../managers/searchIndex";

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

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const id = window.setInterval(() => searchIndex.refresh(), 60_000);
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <Ctx.Provider
      value={{
        paletteOpen,
        openPalette: () => setPaletteOpen(true),
        closePalette: () => setPaletteOpen(false),
      }}
    >
      {children}
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </Ctx.Provider>
  );
}
