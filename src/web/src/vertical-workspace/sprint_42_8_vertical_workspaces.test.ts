/**
 * Sprint 42.8 — Universal Vertical Workspace Framework tests.
 * Updated Sprint 49.0 — Cafe vertical + Beauty/OTC business nav.
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
  "beauty",
  "cafe",
  "crypto",
  "legal",
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
      expect(
        v.nav.every(
          (n) =>
            hasCyrillic(n.label) ||
            n.label.includes("AI") ||
            n.label === "VIN" ||
            n.label === "AML" ||
            n.label === "OTC" ||
            n.label.startsWith("OTC"),
        ),
      ).toBe(true);
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
      expect.arrayContaining(["AI Консьерж", "Контроль рисков", "Мониторинг курсов"]),
    );
    const drone = getVertical("drone")!;
    expect(drone.agents.map((a) => a.name)).toEqual(
      expect.arrayContaining(["Инженер", "Конструктор", "Проектировщик", "Контроль производства"]),
    );
  });
});

describe("Sprint 46.6 / 49.0 vertical navigation stabilization", () => {
  it("Beauty is its own vertical with operational salon nav", () => {
    const beauty = getVertical("beauty");
    expect(beauty).toBeDefined();
    expect(beauty!.id).not.toBe("production");
    expect(beauty!.legacyRoute).toBe("/workspace/beauty");
    const navIds = beauty!.nav.map((n) => n.id);
    expect(navIds).toEqual(
      expect.arrayContaining(["bookings", "calendar", "clients", "staff", "services", "sales"]),
    );
  });

  it("Cafe is a registered venue vertical", () => {
    const cafe = getVertical("cafe");
    expect(cafe).toBeDefined();
    expect(cafe!.legacyRoute).toBe("/workspace/cafe");
    const navIds = cafe!.nav.map((n) => n.id);
    expect(navIds).toEqual(
      expect.arrayContaining(["orders", "menu", "shifts", "bookings", "cashier"]),
    );
  });

  it("Crypto OTC is trader-oriented without unrelated vertical matrix nav", () => {
    const crypto = getVertical("crypto")!;
    const navIds = crypto.nav.map((n) => n.id);
    expect(navIds).toEqual(
      expect.arrayContaining(["pairs", "charts", "quotes", "deals", "analysis"]),
    );
    expect(navIds).not.toEqual(expect.arrayContaining(["automotive", "beauty", "cafe", "agriculture"]));
    expect(crypto.purpose.toLowerCase()).toContain("otc");
  });

  it("Auto exposes insurance/leasing/credit alongside cars", () => {
    const auto = getVertical("auto")!;
    const navIds = auto.nav.map((n) => n.id);
    expect(navIds).toEqual(expect.arrayContaining(["cars", "insurance", "leasing", "credit"]));
  });

  it("Agro exposes buy/sell marketplace nav alongside (not instead of) farm-ops", () => {
    const agro = getVertical("agro")!;
    const navIds = agro.nav.map((n) => n.id);
    expect(navIds).toEqual(
      expect.arrayContaining(["goods", "counterparties", "contracts", "deals", "fields", "machinery"]),
    );
  });

  it("sectionPath resolves distinct routes per vertical (no cross-vertical bleed)", () => {
    expect(sectionPath("beauty", "bookings")).toBe("/workspace/beauty?view=bookings");
    expect(sectionPath("auto", "insurance")).toBe("/vertical/auto/insurance");
    expect(sectionPath("agro", "goods")).toBe("/vertical/agro/goods");
    expect(sectionPath("beauty", "bookings")).not.toBe(sectionPath("auto", "insurance"));
  });
});
