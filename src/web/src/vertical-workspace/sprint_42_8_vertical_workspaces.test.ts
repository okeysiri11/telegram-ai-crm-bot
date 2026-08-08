/**
 * Sprint 42.8 — Universal Vertical Workspace Framework tests.
 */

import { describe, expect, it } from "vitest";
import {
  VERTICAL_WORKSPACES,
  getVertical,
  sectionPath,
  verticalHomePath,
} from "@/vertical-workspace/catalog";

const REQUIRED_IDS = [
  "owner",
  "crm",
  "auto",
  "crypto",
  "travel",
  "drone",
  "agro",
  "construction",
  "production",
  "knowledge",
  "documents",
  "marketplace",
  "ai_studio",
] as const;

function hasCyrillic(s: string): boolean {
  return /[А-Яа-яЁё]/.test(s);
}

describe("Sprint 42.8 Universal Vertical Workspaces", () => {
  it("registers all required verticals", () => {
    expect(VERTICAL_WORKSPACES.map((v) => v.id).sort()).toEqual([...REQUIRED_IDS].sort());
  });

  it("every vertical has RU nav, agents, AI guide and stats", () => {
    for (const v of VERTICAL_WORKSPACES) {
      expect(v.nav.length).toBeGreaterThanOrEqual(4);
      expect(v.agents.some((a) => a.id === "concierge" && a.name.includes("Консьерж"))).toBe(true);
      expect(v.agents.length).toBeGreaterThanOrEqual(2);
      expect(v.stats.length).toBeGreaterThanOrEqual(2);
      expect(v.quickActions.length).toBeGreaterThanOrEqual(1);
      expect(v.aiGuide.bullets.length).toBeGreaterThanOrEqual(2);
      expect(hasCyrillic(v.aiGuide.greeting)).toBe(true);
      expect(v.nav.every((n) => hasCyrillic(n.label) || n.label.includes("AI") || n.label === "VIN" || n.label === "AML" || n.label === "OTC")).toBe(
        true,
      );
      for (const a of v.agents) {
        expect(hasCyrillic(a.name) || a.name.includes("AI")).toBe(true);
        expect(hasCyrillic(a.role)).toBe(true);
      }
    }
  });

  it("AI Concierge is present and identical role across verticals", () => {
    const names = VERTICAL_WORKSPACES.map(
      (v) => v.agents.find((a) => a.id === "concierge")?.name,
    );
    expect(names.every((n) => n === "AI Консьерж")).toBe(true);
  });

  it("routes resolve for home and sections", () => {
    expect(verticalHomePath("crm")).toBe("/vertical/crm");
    expect(sectionPath("auto", "vin")).toBe("/vertical/auto/vin");
    expect(sectionPath("crm", "clients")).toBe("/crm?view=clients");
    expect(getVertical("travel")?.label).toBe("Travel");
  });

  it("crypto and drone specialists match product brief", () => {
    const crypto = getVertical("crypto")!;
    expect(crypto.agents.map((a) => a.name)).toEqual(
      expect.arrayContaining([
        "AI Консьерж",
        "Контроль AML",
        "Поиск арбитража",
        "Контроль рисков",
        "Мониторинг курсов",
        "Контроль ликвидности",
      ]),
    );
    const drone = getVertical("drone")!;
    expect(drone.agents.map((a) => a.name)).toEqual(
      expect.arrayContaining(["Инженер", "Конструктор", "Проектировщик", "Контроль производства"]),
    );
  });
});
