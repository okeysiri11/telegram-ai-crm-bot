import { COMMAND_CATALOG } from "./quickActions";
import { contextEngine } from "./contextEngine";

const usage = new Map<string, number>();

export function recordCommandUse(id: string) {
  usage.set(id, (usage.get(id) ?? 0) + 1);
}

export const smartSuggestions = {
  list(limit = 8) {
    const ctx = contextEngine.get();
    const hour = new Date().getHours();
    const favorites = new Set(["open_crm", "open_workspace", "create_task"]);
    return COMMAND_CATALOG.map((c) => {
      let score = 0;
      if (favorites.has(c.action)) score += 0.35;
      score += Math.min(usage.get(c.id) ?? 0, 10) / 20;
      if (ctx.currentModule && c.action.includes(String(ctx.currentModule).replace(/\W/g, "_"))) score += 0.15;
      if (ctx.role === "owner" && (c.kind === "create" || c.kind === "open")) score += 0.1;
      if (hour >= 9 && hour <= 11 && c.kind === "open") score += 0.05;
      if (hour >= 14 && hour <= 17 && c.kind === "create") score += 0.05;
      return { ...c, score };
    })
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  },
};
