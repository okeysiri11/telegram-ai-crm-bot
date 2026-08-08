/**
 * Sprint 42.9 — Owner Experience, AI Chat & Human-First Workflow.
 */

import { describe, expect, it } from "vitest";
import {
  WORK_AS_OPTIONS,
  workAsFromViewMode,
  workAsLabel,
} from "@/owner-experience/workAsCatalog";
import { CREATE_ITEMS } from "@/owner-experience/QuickCreatePanel";
import { DESKTOP_APPS } from "@/enterprise-desktop/desktopCatalog";
import { ENTERPRISE_SHELL_NAV } from "@/shell/enterprise/enterpriseNav";
import { VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";
import { PRODUCTION_STUDIOS } from "@/ai-production-studio/productionCatalog";

function hasCyrillic(s: string): boolean {
  return /[А-Яа-яЁё]/.test(s);
}

describe("Sprint 42.9 Owner Identity & Work-As", () => {
  it("exposes all work-as personas in Russian", () => {
    expect(WORK_AS_OPTIONS.map((o) => o.id)).toEqual([
      "platform_owner",
      "ceo",
      "manager",
      "operator",
      "client",
      "partner",
      "demo",
    ]);
    for (const o of WORK_AS_OPTIONS) {
      expect(hasCyrillic(o.label)).toBe(true);
      expect(o.viewMode).toBeTruthy();
      expect(o.roleSwitcherId).toBeTruthy();
    }
  });

  it("maps view modes to work-as personas", () => {
    expect(workAsFromViewMode("platform_owner")).toBe("platform_owner");
    expect(workAsFromViewMode("company_admin")).toBe("ceo");
    expect(workAsFromViewMode("manager")).toBe("manager");
    expect(workAsFromViewMode("client")).toBe("client");
    expect(workAsLabel("ceo")).toBe("CEO организации");
  });
});

describe("Sprint 42.9 AI context & quick create", () => {
  it("every vertical has Concierge specialist roster", () => {
    for (const v of VERTICAL_WORKSPACES) {
      expect(v.agents.some((a) => a.id === "concierge")).toBe(true);
      expect(v.agents.length).toBeGreaterThanOrEqual(2);
    }
  });

  it("quick create exposes required object types", () => {
    expect(CREATE_ITEMS).toHaveLength(7);
    expect(CREATE_ITEMS.map((i) => i.label)).toEqual([
      "Клиента",
      "Документ",
      "Проект",
      "AI-задачу",
      "Напоминание",
      "Сделку",
      "Контакт",
    ]);
  });

  it("maps vertical context to specialist AI", async () => {
    const { specialistForVertical } = await import("@/owner-experience/ContextualAiChat");
    expect(specialistForVertical("crm")).toBe("CRM AI");
    expect(specialistForVertical("auto")).toBe("Auto AI");
    expect(specialistForVertical("crypto")).toBe("Crypto AI");
    expect(specialistForVertical("drone")).toBe("Drone AI");
    expect(specialistForVertical("travel")).toBe("Travel AI");
  });
});

describe("Sprint 42.9 Russian localization surfaces", () => {
  it("launcher apps are mostly Russian (acronyms allowed)", () => {
    const acronyms = new Set(["CRM", "ERP", "AI", "OTC", "AML", "VIN", "MCP"]);
    for (const app of DESKTOP_APPS) {
      const ok =
        hasCyrillic(app.label) ||
        [...acronyms].some((a) => app.label.includes(a)) ||
        app.label === "Reels";
      expect(ok, app.label).toBe(true);
    }
  });

  it("shell nav labels are Russian", () => {
    for (const n of ENTERPRISE_SHELL_NAV) {
      const ok =
        hasCyrillic(n.label) || n.label === "CRM" || n.label === "ERP" || n.label.includes("AI");
      expect(ok, n.label).toBe(true);
    }
  });

  it("production studios have Russian labels", () => {
    for (const s of PRODUCTION_STUDIOS.slice(0, 12)) {
      expect(hasCyrillic(s.label) || s.label.includes("Reels") || s.label.includes("AI")).toBe(true);
    }
  });
});
