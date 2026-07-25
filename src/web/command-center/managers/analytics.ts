import { recordCommandUse } from "./suggestions";

type AnalyticEvent = {
  id: string;
  ok: boolean;
  elapsedMs: number;
  ai?: boolean;
};

const events: AnalyticEvent[] = [];

export const commandAnalytics = {
  track(id: string, ok: boolean, elapsedMs: number, ai = false) {
    recordCommandUse(id);
    events.push({ id, ok, elapsedMs, ai });
    if (events.length > 500) events.shift();
  },
  snapshot() {
    const usage: Record<string, number> = {};
    let success = 0;
    let fail = 0;
    let ai = 0;
    const times: Record<string, number[]> = {};
    for (const e of events) {
      usage[e.id] = (usage[e.id] ?? 0) + 1;
      if (e.ok) success += 1;
      else fail += 1;
      if (e.ai) ai += 1;
      (times[e.id] ??= []).push(e.elapsedMs);
    }
    const popular = Object.entries(usage)
      .map(([id, count]) => ({ id, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15);
    const avgTime: Record<string, number> = {};
    for (const [id, arr] of Object.entries(times)) {
      avgTime[id] = Math.round((arr.reduce((s, n) => s + n, 0) / arr.length) * 1000) / 1000;
    }
    return {
      command_usage: usage,
      execution_time_ms: avgTime,
      ai_usage: ai,
      success_rate: success + fail ? success / (success + fail) : 1,
      errors: fail,
      popular_commands: popular,
      recommendations: ["pin_top_commands_to_favorites", "enable_ai_command_shortcuts"],
    };
  },
};
