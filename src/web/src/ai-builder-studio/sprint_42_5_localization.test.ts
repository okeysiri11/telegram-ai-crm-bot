/**
 * Sprint 42.5 — Full Russian localization audit tests.
 */

import { describe, expect, it } from "vitest";
import { PLATFORM_GLOSSARY, BUILDER_NAV_RU, term, builderDisplayName } from "@/i18n/platformGlossary";
import { BUILDER_UI_RU, bu } from "../../platform-builder/i18n/builderUiRu";
import { CONCIERGE_V2_STEPS, V2_ROLES, V2_STYLES } from "../../platform-builder/concierge/catalogV2";
import { CONCIERGE_WIZARD_STEPS, ROLES as CONCIERGE_ROLES } from "../../platform-builder/concierge/catalog";
import { AI_WIZARD_STEPS, PROFESSIONS, WHY_MULTI } from "../../platform-builder/ai-builder/catalog";
import { UBF_STEPS, LIFECYCLE } from "../../platform-builder/ubf/catalog";
import { HUB_CARDS, DOMAIN_SKILL_PACKS, PROMPT_LIBRARY } from "@/ai-builder-studio/studioCatalog";

function hasCyrillic(s: string): boolean {
  return /[А-Яа-яЁё]/.test(s);
}

describe("Sprint 42.5 Full Russian Localization", () => {
  it("platform glossary exposes required RU terms", () => {
    expect(term("dashboard")).toBe("Панель управления");
    expect(term("workflow")).toBe("Сценарий");
    expect(term("preview")).toBe("Предпросмотр");
    expect(term("comingSoon")).toBe("Скоро");
    expect(term("visualIntelligence")).toBe("Визуальный интеллект");
    expect(term("dataFabric")).toBe("Шина данных");
    expect(PLATFORM_GLOSSARY.enterprise).toBe("Предприятие");
    expect(Object.keys(BUILDER_NAV_RU).length).toBeGreaterThan(40);
    expect(builderDisplayName("concierge")).toMatch(/Консьерж/);
  });

  it("builder UI dictionary covers chrome actions", () => {
    expect(bu("create")).toBe("Создать");
    expect(bu("preview")).toBe("Предпросмотр");
    expect(bu("cancel")).toBe("Отмена");
    expect(BUILDER_UI_RU.liveValidation).toMatch(/Проверка/);
  });

  it("Concierge catalogs are fully Russian (V1 + V2)", () => {
    expect(CONCIERGE_V2_STEPS.every(hasCyrillic)).toBe(true);
    expect(CONCIERGE_WIZARD_STEPS.every(hasCyrillic)).toBe(true);
    expect(V2_STYLES.every((s) => hasCyrillic(s.name) && hasCyrillic(s.sample))).toBe(true);
    expect(CONCIERGE_ROLES.every((r) => hasCyrillic(r.name))).toBe(true);
    expect(V2_ROLES.some((r) => r.name === "Консьерж")).toBe(true);
  });

  it("AI Agent Builder catalog and why-multi copy are Russian", () => {
    expect(AI_WIZARD_STEPS.every(hasCyrillic)).toBe(true);
    expect(hasCyrillic(WHY_MULTI.title)).toBe(true);
    expect(hasCyrillic(WHY_MULTI.summary)).toBe(true);
    expect(PROFESSIONS.every((p) => hasCyrillic(p.name) || ["CRM", "ERP", "Crypto"].includes(p.name))).toBe(
      true,
    );
  });

  it("Universal Builder Framework steps are Russian", () => {
    expect(UBF_STEPS.every(hasCyrillic)).toBe(true);
    expect(LIFECYCLE.every(hasCyrillic)).toBe(true);
  });

  it("AI Studio hub packs and prompts are Russian-first", () => {
    expect(HUB_CARDS.every((c) => hasCyrillic(c.title) || c.title.includes("AI"))).toBe(true);
    expect(DOMAIN_SKILL_PACKS.every((p) => hasCyrillic(p.title) || p.title === "CRM")).toBe(true);
    expect(PROMPT_LIBRARY.every((p) => hasCyrillic(p.title))).toBe(true);
  });

  it("critical surface catalogs satisfy zero-English gate prerequisites", () => {
    expect(HUB_CARDS).toHaveLength(4);
    expect(CONCIERGE_V2_STEPS).toHaveLength(7);
    expect(AI_WIZARD_STEPS.every(hasCyrillic)).toBe(true);
    expect(UBF_STEPS.every(hasCyrillic)).toBe(true);
  });
});
