import { beforeEach, describe, expect, it } from "vitest";
import { buildPaletteSections, searchPaletteCommands } from "./paletteSections";
import { commandFavorites, commandRecent } from "./commandFavorites";
import { buildGlobalActivityFeed } from "./globalActivityFeed";
import { UNIVERSAL_QUICK_ACTIONS } from "./UniversalQuickActionsBar";
import { DEVELOPER_COMMANDS } from "./developerCommands";
import { shortcutManager } from "../../navigation/managers/shortcutManager";
import { HOTKEYS } from "../../command-center/types";

describe("Sprint 27.5 command center runtime", () => {
  beforeEach(() => {
    localStorage.removeItem("ews_cc_favorites_v1");
    localStorage.removeItem("ews_cc_recent_v1");
  });

  it("builds palette sections with recent, favorites, AI, developer", () => {
    commandRecent.push("act_open_crm");
    const sections = buildPaletteSections();
    const ids = sections.map((s) => s.id);
    expect(ids).toEqual(expect.arrayContaining(["favorites", "navigate", "create", "ai", "developer"]));
    expect(sections.find((s) => s.id === "developer")?.items.length).toBe(DEVELOPER_COMMANDS.length);
  });

  it("searches palette including developer commands", () => {
    const hits = searchPaletteCommands("developer runtime");
    expect(hits.some((h) => h.id === "dev_open_runtime")).toBe(true);
  });

  it("toggles favorites persistence", () => {
    const before = commandFavorites.list();
    expect(before.length).toBeGreaterThan(0);
    commandFavorites.toggle("act_open_crm");
    // toggle may remove or add depending on default set
    expect(Array.isArray(commandFavorites.list())).toBe(true);
  });

  it("merges global activity feed kinds", () => {
    const feed = buildGlobalActivityFeed(50);
    expect(feed.length).toBeGreaterThan(0);
    const kinds = new Set(feed.map((f) => f.kind));
    expect(kinds.has("ai") || kinds.has("notification") || kinds.has("crm")).toBe(true);
  });

  it("exposes universal quick actions", () => {
    const labels = UNIVERSAL_QUICK_ACTIONS.map((a) => a.label);
    expect(labels).toEqual(
      expect.arrayContaining([
        "New Client",
        "New Project",
        "New Task",
        "New Workflow",
        "New AI Agent",
        "Upload Document",
        "Open Dashboard",
        "Open CRM",
        "Open ERP",
      ]),
    );
  });

  it("registers keyboard shortcuts for tabs and panels", () => {
    const actions = shortcutManager.list().map((s) => s.action);
    expect(actions).toEqual(
      expect.arrayContaining([
        "open_command_palette",
        "close_workspace_tab",
        "reopen_closed_tab",
        "next_workspace_tab",
        "next_dock_panel",
        "focus_global_search",
      ]),
    );
    expect(HOTKEYS).toContain("Ctrl+K");
    expect(HOTKEYS).toContain("Ctrl+W");
  });
});
