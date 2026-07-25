import { describe, expect, it } from "vitest";
import {
  NAVIGATION_VERSION,
  breadcrumbEngine,
  buildNavigationDashboard,
  commandPalette,
  menuEngine,
  navigationManager,
  navigationPerformance,
  searchProvider,
  shortcutManager,
} from "../../navigation";

describe("Enterprise Navigation Platform", () => {
  it("exposes version and palette hotkeys", () => {
    expect(NAVIGATION_VERSION).toBe("9.0.4");
    expect(commandPalette.hotkeys).toContain("Ctrl+K");
    expect(commandPalette.search("ai").length).toBeGreaterThan(0);
  });

  it("covers menu, search, breadcrumbs, shortcuts, performance", () => {
    expect(navigationManager.surfaces()).toContain("sidebar");
    expect(menuEngine.groups().length).toBeGreaterThan(0);
    expect(searchProvider.search("crm")[0]?.category).toBe("crm");
    expect(breadcrumbEngine.fromPath("/identity/users").some((c) => c.level === "module")).toBe(true);
    expect(shortcutManager.list().some((s) => s.action === "open_command_palette")).toBe(true);
    expect(navigationPerformance.features).toContain("search_caching");
  });

  it("builds navigation dashboard", () => {
    const dash = buildNavigationDashboard();
    expect(dash.activeNavigation.length).toBeGreaterThan(0);
    expect(dash.commandUsage.length).toBeGreaterThan(0);
  });
});
