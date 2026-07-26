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
    const favorites = new Set(["open_crm", "open_workspace", "create_task", "open_mission_control", "open_concierge"]);
    const module = String(ctx.currentModule || "");
    return COMMAND_CATALOG.map((c) => {
      let score = 0;
      if (favorites.has(c.action)) score += 0.35;
      score += Math.min(usage.get(c.id) ?? 0, 10) / 20;
      if (module && (c.route?.includes(module) || c.action.includes(module) || c.keywords?.includes(module))) {
        score += 0.25;
      }
      if (module === "crm" && (c.action.includes("crm") || c.action.includes("client"))) score += 0.2;
      if (module === "city" && c.action.includes("city")) score += 0.2;
      if (module === "ai" && (c.action.includes("ai") || c.action.includes("concierge"))) score += 0.2;
      if (ctx.role === "owner" || ctx.role === "executive" || ctx.role === "business_owner") {
        if (c.action.includes("dashboard") || c.action.includes("mission")) score += 0.15;
      }
      if (hour >= 9 && hour <= 11 && c.kind === "open") score += 0.05;
      if (hour >= 14 && hour <= 17 && c.kind === "create") score += 0.05;
      return { ...c, score };
    })
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  },
};
