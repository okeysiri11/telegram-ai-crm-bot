/**
 * Sprint 42.4 — Russian-First Platform & AI Builder redesign tests.
 */

import { describe, expect, it } from "vitest";
import { PLATFORM_GLOSSARY, localizeLabel, term } from "@/i18n/platformGlossary";
import { HUB_CARDS, STUDIO_HOME_CARDS } from "@/ai-builder-studio/studioCatalog";
import {
  CONCIERGE_V2_STEPS,
  V2_ROLES,
  V2_SKILLS,
  V2_MODULES,
  V2_PERMISSIONS,
  emptyConciergeV2,
  previewReply,
  v2ToApiDraft,
} from "../../platform-builder/concierge/catalogV2";
import { AI_WIZARD_STEPS } from "../../platform-builder/ai-builder/catalog";
import { isRouteAllowedForViewMode } from "@/ux-revolution";

describe("Sprint 42.4 Russian-First AI Builder", () => {
  it("glossary covers core platform terms in Russian", () => {
    expect(term("dashboard")).toBe("Панель управления");
    expect(term("builder")).toBe("Конструктор");
    expect(term("workflow")).toBe("Сценарий");
    expect(term("knowledge")).toBe("База знаний");
    expect(term("commandCenter")).toBe("Центр управления");
    expect(localizeLabel("Dashboard")).toBe(PLATFORM_GLOSSARY.dashboard);
    expect(localizeLabel("AI")).toBe("AI"); // acronyms stay if not mapped — OK via passthrough
  });

  it("AI Builder hub has exactly four primary cards", () => {
    expect(HUB_CARDS).toHaveLength(4);
    expect(HUB_CARDS.map((c) => c.id)).toEqual(["concierge", "team", "settings", "integrations"]);
    expect(HUB_CARDS.every((c) => /[А-Яа-яЁё]/.test(c.title) || c.title.includes("AI"))).toBe(true);
  });

  it("Concierge Wizard 2.0 has 7 RU steps and required option sets", () => {
    expect(CONCIERGE_V2_STEPS).toHaveLength(7);
    expect(CONCIERGE_V2_STEPS[0]).toBe("Имя и образ");
    expect(CONCIERGE_V2_STEPS[6]).toBe("Тестовый диалог");
    expect(V2_ROLES.some((r) => r.name === "Консьерж")).toBe(true);
    expect(V2_SKILLS.some((s) => s.name === "CRM")).toBe(true);
    expect(V2_MODULES.length).toBeGreaterThanOrEqual(8);
    expect(V2_PERMISSIONS.some((p) => p.id === "run_workflows")).toBe(true);
  });

  it("maps V2 draft to API payload and preview reply is Russian", () => {
    const d = emptyConciergeV2();
    d.name = "Алекс";
    d.role = "manager";
    const api = v2ToApiDraft(d);
    expect(api.name).toBe("Алекс");
    expect(api.voice_profile).toBeTruthy();
    const reply = previewReply(d, "Привет");
    expect(reply).toContain("Алекс");
    expect(reply).toMatch(/Менеджер|Консьерж/);
  });

  it("agent wizard steps are Russian", () => {
    expect(AI_WIZARD_STEPS[0]).toBe("Количество");
    expect(AI_WIZARD_STEPS[AI_WIZARD_STEPS.length - 1]).toBe("Готово");
    expect(AI_WIZARD_STEPS.every((s) => /[А-Яа-яЁё]/.test(s))).toBe(true);
  });

  it("studio secondary cards titles are Russian-first", () => {
    expect(STUDIO_HOME_CARDS.find((c) => c.id === "knowledge")?.title).toBe("База знаний");
    expect(STUDIO_HOME_CARDS.find((c) => c.id === "workflow")?.title).toBe("Сценарии");
  });

  it("clients cannot open builders; owners can", () => {
    expect(isRouteAllowedForViewMode("/platform-builder/concierge", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/platform-builder/builder-studio", "manager")).toBe(false);
    expect(isRouteAllowedForViewMode("/platform-builder/concierge", "platform_owner")).toBe(true);
    expect(isRouteAllowedForViewMode("/platform-builder/builder-studio", "developer")).toBe(true);
    expect(isRouteAllowedForViewMode("/ai-agents", "client")).toBe(true);
  });
});
