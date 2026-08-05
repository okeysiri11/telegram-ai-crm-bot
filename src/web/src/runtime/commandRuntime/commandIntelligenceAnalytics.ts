/**
 * Command analytics intelligence — Sprint 28.7.
 * Extends legacy commandAnalytics with favorites · errors · AI usage.
 */

import { commandAnalytics } from "../../../command-center/managers/analytics";
import { commandHistory } from "./commandHistory";
import type { CommandAnalyticsSnapshot } from "./commandTypes";

export const COMMAND_ANALYTICS_KEY = "ews_cmd_analytics_v1";

type ErrorHit = { id: string; error: string; at: string };

const errors: ErrorHit[] = [];
let aiCount = 0;

export const commandIntelligenceAnalytics = {
  track(id: string, ok: boolean, elapsedMs: number, opts?: { ai?: boolean; error?: string }) {
    commandAnalytics.track(id, ok, elapsedMs, Boolean(opts?.ai));
    if (opts?.ai) aiCount += 1;
    if (!ok && opts?.error) {
      errors.unshift({ id, error: opts.error, at: new Date().toISOString() });
      if (errors.length > 100) errors.length = 100;
    }
  },

  snapshot(): CommandAnalyticsSnapshot {
    const base = commandAnalytics.snapshot();
    const usage = base.command_usage || {};
    const times = Object.values(base.execution_time_ms || {}) as number[];
    const avg =
      times.length > 0 ? Math.round((times.reduce((a, b) => a + b, 0) / times.length) * 100) / 100 : 0;
    const executionCount = Object.values(usage).reduce((a, b) => a + b, 0);

    return {
      executionCount,
      successRate: base.success_rate,
      failures: base.errors,
      avgDurationMs: avg,
      usage,
      favorites: commandHistory.favorites(),
      aiUsage: base.ai_usage || aiCount,
      popular: base.popular_commands || [],
      errors: errors.slice(0, 20),
    };
  },

  persist() {
    try {
      localStorage.setItem(
        COMMAND_ANALYTICS_KEY,
        JSON.stringify({ at: new Date().toISOString(), ...this.snapshot() }),
      );
    } catch {
      /* ignore */
    }
  },
};
