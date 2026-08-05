import { fuzzyScore } from "./fuzzy";
import { COMMAND_CATALOG } from "./quickActions";
import { contextEngine } from "./contextEngine";
import { navigationIndex } from "./omnibox";
import { interpretAiIntent } from "@/runtime/commandRuntime/aiIntentRouter";
import { commandRuntime } from "@/runtime/commandRuntime";

/**
 * Legacy AI command center — Sprint 28.7 routes execution through Command Runtime.
 * `interpret` remains for UI preview; `execute` is the only action path.
 */
export const aiCommandCenter = {
  interpret(utterance: string): { ok: boolean; intent?: string; route?: string; label?: string } {
    const r = interpretAiIntent(utterance);
    if (r.ok && r.intent) {
      const cmd = COMMAND_CATALOG.find((c) => c.action === r.intent);
      if (cmd?.route || r.route) {
        try {
          navigationIndex.recordUse(cmd?.id ?? r.intent);
        } catch {
          /* ignore */
        }
      }
      // Keep contextEngine conversation log (also done in interpretAiIntent)
      void contextEngine;
    }
    return { ok: r.ok, intent: r.intent, route: r.route, label: r.label };
  },

  async execute(utterance: string) {
    return commandRuntime.routeAiIntent(utterance);
  },

  /** Fuzzy fallback retained for diagnostics */
  fuzzy(utterance: string) {
    let best: { action: string; score: number } | null = null;
    for (const c of COMMAND_CATALOG) {
      const score = fuzzyScore(utterance, `${c.label} ${c.action}`);
      if (!best || score > best.score) best = { action: c.action, score };
    }
    return best;
  },
};
