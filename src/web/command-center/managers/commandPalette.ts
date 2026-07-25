import { fuzzyScore } from "./fuzzy";
import { COMMAND_CATALOG, quickActionsEngine } from "./quickActions";
import type { CommandItem } from "../types";

export const commandPaletteEngine = {
  hotkeys: ["Ctrl+K", "Meta+K", "Ctrl+P", "Ctrl+Shift+P", "Ctrl+Space", "Ctrl+/"] as const,
  list(): CommandItem[] {
    return quickActionsEngine.list();
  },
  search(query: string): CommandItem[] {
    const q = query.trim();
    if (!q) return this.list();
    return COMMAND_CATALOG
      .map((c) => {
        const hay = [c.label, c.action, c.kind, ...c.keywords].join(" ");
        return { c, score: fuzzyScore(q, hay) };
      })
      .filter((x) => x.score >= 0.3)
      .sort((a, b) => b.score - a.score)
      .map((x) => x.c);
  },
};
