import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UniversalCommandPalette } from "./UniversalCommandPalette";
import { Omnibox } from "./Omnibox";
import { contextEngine } from "../managers/contextEngine";

type CcUi = {
  openPalette: () => void;
  openOmnibox: () => void;
  openAi: () => void;
  close: () => void;
  paletteOpen: boolean;
  omniboxOpen: boolean;
};

const Ctx = createContext<CcUi | null>(null);

export function useCommandCenterUi() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCommandCenterUi requires CommandCenterProvider");
  return ctx;
}

export function CommandCenterProvider({ children }: { children: ReactNode }) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [omniboxOpen, setOmniboxOpen] = useState(false);
  const [aiMode, setAiMode] = useState(false);

  const openPalette = useCallback(() => {
    setAiMode(false);
    setPaletteOpen(true);
  }, []);
  const openOmnibox = useCallback(() => setOmniboxOpen(true), []);
  const openAi = useCallback(() => {
    setAiMode(true);
    setPaletteOpen(true);
  }, []);
  const close = useCallback(() => {
    setPaletteOpen(false);
    setOmniboxOpen(false);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;
      const key = e.key.toLowerCase();
      if (meta && key === "k") {
        e.preventDefault();
        setAiMode(false);
        setOmniboxOpen(false);
        setPaletteOpen(true);
      }
      if (meta && key === "p" && !e.shiftKey) {
        e.preventDefault();
        setOmniboxOpen(true);
        setPaletteOpen(false);
      }
      if (meta && e.shiftKey && key === "p") {
        e.preventDefault();
        setAiMode(true);
        setPaletteOpen(true);
        setOmniboxOpen(false);
      }
      if (meta && e.code === "Space") {
        e.preventDefault();
        setPaletteOpen(true);
      }
      if (meta && key === "/") {
        e.preventDefault();
        setOmniboxOpen(true);
        setPaletteOpen(false);
      }
      if (e.key === "Escape") {
        setPaletteOpen(false);
        setOmniboxOpen(false);
        setAiMode(false);
      }
    };
    window.addEventListener("keydown", onKey);
    contextEngine.patch({ workspace: "default" });
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const value = useMemo(
    () => ({
      paletteOpen,
      omniboxOpen,
      openPalette,
      openOmnibox,
      openAi,
      close,
    }),
    [paletteOpen, omniboxOpen, openPalette, openOmnibox, openAi, close],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <UniversalCommandPalette
        open={paletteOpen}
        initialMode={aiMode ? "ai" : "palette"}
        onClose={() => {
          setPaletteOpen(false);
          setAiMode(false);
        }}
      />
      <Omnibox open={omniboxOpen} onClose={() => setOmniboxOpen(false)} />
    </Ctx.Provider>
  );
}
