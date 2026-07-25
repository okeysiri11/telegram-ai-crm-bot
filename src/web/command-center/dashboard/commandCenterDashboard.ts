import { PRODUCTIVITY_WIDGETS } from "./widgets";
import { commandAnalytics } from "../managers/analytics";
import { smartSuggestions } from "../managers/suggestions";
import { navigationIndex } from "../managers/omnibox";
import { HOTKEYS, COMMAND_CENTER_VERSION } from "../types";
import { contextEngine } from "../managers/contextEngine";

export const PRODUCTIVITY_WIDGET_IDS = [
  "recent_activity",
  "pinned_objects",
  "favorites",
  "drafts",
  "clipboard_history",
  "notifications",
  "reminder_center",
  "scheduled_actions",
  "quick_notes",
  "recently_opened",
  "recent_searches",
  "most_used_commands",
] as const;

export function buildCommandCenterDashboard() {
  const analytics = commandAnalytics.snapshot();
  const suggestions = smartSuggestions.list(5);
  const ctx = contextEngine.get();
  return {
    version: COMMAND_CENTER_VERSION,
    ready: true,
    widgets: PRODUCTIVITY_WIDGET_IDS,
    hotkeys: HOTKEYS,
    analytics,
    suggestions,
    context: ctx,
    index_count: navigationIndex.list().length,
    integrations: ["workspace", "dashboard", "navigation", "ai", "marketplace"],
  };
}

export { PRODUCTIVITY_WIDGETS };
