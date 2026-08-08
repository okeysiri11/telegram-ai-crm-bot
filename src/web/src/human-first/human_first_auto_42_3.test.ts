/**
 * Sprint 42.3 — Human-First Auto UX acceptance.
 */

import { beforeEach, describe, expect, it } from "vitest";
import { MODULE_LANDINGS } from "@/modules/moduleLandingCatalog";
import { AUTO_AI_CHIPS, AUTO_AI_INTENTS, matchAutoAiIntent } from "@/human-first/autoAiIntents";
import { useExperienceModeStore, EXPERIENCE_MODE_KEY } from "@/ux-revolution";
import { isRouteAllowedForViewMode } from "@/ux-revolution";

describe("Sprint 42.3 Human-First Auto", () => {
  beforeEach(() => {
    localStorage.clear();
    useExperienceModeStore.setState({ mode: "simple" });
  });

  it("defaults to simple experience mode", () => {
    expect(useExperienceModeStore.getState().mode).toBe("simple");
    expect(localStorage.getItem(EXPERIENCE_MODE_KEY)).toBeNull();
  });

  it("auto landing has short AI guide and fix CTA", () => {
    const auto = MODULE_LANDINGS.find((m) => m.id === "auto");
    expect(auto).toBeTruthy();
    expect(auto!.aiGuide.bullets).toEqual(["Новые заявки", "Сделки", "Автомобили без фото"]);
    expect(auto!.aiGuide.recommendedAction.label).toBe("Исправить");
    expect(auto!.primaryAction.label).toBe("Добавить автомобиль");
    expect(auto!.actions.map((a) => a.label)).toEqual([
      "Автомобили",
      "Клиенты",
      "Продажи",
      "Импорт",
      "Склад",
    ]);
  });

  it("matches Auto AI chip phrases to actions", () => {
    expect(matchAutoAiIntent("Добавь автомобиль")?.route).toContain("action=vehicle");
    expect(matchAutoAiIntent("Найди клиента")?.route).toContain("view=clients");
    expect(matchAutoAiIntent("Покажи продажи")?.route).toContain("view=sales");
    expect(matchAutoAiIntent("Импортируй VIN")?.route).toContain("import");
    expect(matchAutoAiIntent("Создай договор")?.label).toMatch(/договор/i);
    expect(AUTO_AI_CHIPS).toHaveLength(5);
    expect(AUTO_AI_INTENTS.length).toBeGreaterThanOrEqual(5);
  });

  it("platform control center is owner-reachable", () => {
    expect(isRouteAllowedForViewMode("/platform-builder/ops-center", "platform_owner")).toBe(true);
    expect(isRouteAllowedForViewMode("/platform-builder/ops-center", "developer")).toBe(true);
    expect(isRouteAllowedForViewMode("/workspace/auto", "manager")).toBe(true);
  });

  it("platform landing points to control center", () => {
    const platform = MODULE_LANDINGS.find((m) => m.id === "platform");
    expect(platform?.primaryAction.route).toBe("/platform-builder/ops-center");
    expect(platform?.actions.some((a) => a.route.includes("ops-center"))).toBe(true);
  });
});
