/**
 * Sprint 41.2 — interface preferences persistence tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  PREFERENCES_KEY,
  usePreferencesStore,
  applyInterfacePreferences,
} from "@/preferences/preferencesStore";
import { helpForRoute, MODULE_HELP_CATALOG } from "@/help/moduleHelpCatalog";
import { messages } from "@/i18n/messages";

describe("Sprint 41.2 interface preferences", () => {
  beforeEach(() => {
    localStorage.clear();
    usePreferencesStore.setState({
      fontScale: 100,
      density: "standard",
      menuWidth: "standard",
      language: "ru",
      theme: "system",
      timeZone: "UTC",
      dateFormat: "YYYY-MM-DD",
      dashboardLayout: "grid",
      notificationsEnabled: true,
      accessibility: { reduceMotion: false, highContrast: false },
    });
  });

  it("persists font scale density and menu width", () => {
    usePreferencesStore.getState().update({ fontScale: 110, density: "compact", menuWidth: "wide" });
    const raw = localStorage.getItem(PREFERENCES_KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed.fontScale).toBe(110);
    expect(parsed.density).toBe("compact");
    expect(parsed.menuWidth).toBe("wide");
  });

  it("applies CSS variables to document", () => {
    applyInterfacePreferences({
      fontScale: 120,
      density: "comfortable",
      menuWidth: "compact",
      accessibility: { reduceMotion: true, highContrast: false },
    });
    expect(document.documentElement.style.getPropertyValue("--ew-font-scale")).toBe("1.2");
    expect(document.documentElement.dataset.density).toBe("comfortable");
    expect(document.documentElement.dataset.menuWidth).toBe("compact");
  });

  it("covers major modules with help including related", () => {
    expect(MODULE_HELP_CATALOG.length).toBeGreaterThanOrEqual(10);
    expect(helpForRoute("/crm")?.related.length).toBeGreaterThan(0);
    expect(helpForRoute("/documents")?.purpose).toBeTruthy();
    expect(helpForRoute("/settings")?.workflow).toContain("Интерфейс");
  });

  it("has RU interface settings keys", () => {
    for (const k of [
      "iface.title",
      "iface.density",
      "iface.fontScale",
      "page.where",
      "viewMode.hint",
    ]) {
      expect(messages.ru[k]).toBeTruthy();
    }
  });
});
