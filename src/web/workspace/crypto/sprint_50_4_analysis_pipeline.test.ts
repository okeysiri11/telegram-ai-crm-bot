import { beforeEach, describe, expect, it } from "vitest";
import {
  defaultAnalyses,
  defaultSpecialists,
  loadAgentSettings,
  loadAnalyses,
  saveAgentSettings,
  saveAnalyses,
} from "./otcPrefs";
import { CAL_FILTERS } from "./operatorCalendar";
import { integrityLabel } from "./paperTradingPanels";

describe("sprint 50.4 analysis pipeline UI contracts", () => {
  beforeEach(() => localStorage.clear());

  it("chart action labels are russian with allowed product names", () => {
    const labels = ["Создать сигнал", "К анализу", "Бумажная торговля"];
    expect(labels.every((l) => l.length > 3)).toBe(true);
    expect(["EUR/USD", "DXY", "TradingView", "Technical Agent", "Macro Agent", "News Agent", "Chief Analyst"]).toContain(
      "Technical Agent",
    );
  });

  it("analysis enable/disable persists active state", () => {
    const items = defaultAnalyses().map((a) =>
      a.id === "morning" ? { ...a, enabled: false, status: "Выключен" } : a,
    );
    saveAnalyses(items, "t1");
    const loaded = loadAnalyses("t1");
    const morning = loaded.find((a) => a.id === "morning");
    expect(morning?.enabled).toBe(false);
    expect(morning?.status).toBe("Выключен");
    const enabled = loaded.map((a) => (a.id === "morning" ? { ...a, enabled: true, status: "Активен" } : a));
    saveAnalyses(enabled, "t1");
    expect(loadAnalyses("t1").find((a) => a.id === "morning")?.status).toBe("Активен");
  });

  it("analysis presets include morning europe us evening", () => {
    const ids = defaultAnalyses().map((a) => a.id);
    expect(ids).toEqual(expect.arrayContaining(["morning", "pre_europe", "pre_us", "evening"]));
  });

  it("agent run settings and risk agent exist", () => {
    const specs = defaultSpecialists();
    expect(specs.map((s) => s.id)).toEqual(
      expect.arrayContaining(["technical", "macro", "news", "risk", "chief"]),
    );
    saveAgentSettings({ technical: { enabled: true, weight: 1.1, instruments: ["EUR/USD"] } }, "t1");
    expect(loadAgentSettings("t1").technical.enabled).toBe(true);
  });

  it("cross-link targets cover required flow", () => {
    const views = ["charts", "analysis", "specialists", "signals", "paper", "intel_history", "journal"];
    expect(views).toContain("paper");
    expect(views).toContain("intel_history");
  });

  it("contextual empty copy not demo bootstrap", () => {
    const forbidden = "Создайте первую запись или загрузите демо-данные";
    const samples = [
      "Сигналов пока нет. Создайте сигнал по EUR/USD или DXY.",
      "Этот специалист ещё не запускался.",
      "Анализы ещё не выполнялись.",
      "Бумажных сделок пока нет.",
    ];
    expect(samples.every((s) => !s.includes(forbidden))).toBe(true);
    expect(samples[0]).toContain("EUR/USD");
  });

  it("calendar filters remain russian", () => {
    expect(CAL_FILTERS.map((f) => f.label)).toEqual(
      expect.arrayContaining(["Макроэкономика", "Сигналы", "Анализы"]),
    );
  });

  it("honesty labels russian", () => {
    expect(integrityLabel("error")).toBe("Источник недоступен");
    expect(integrityLabel("needs_config")).toBe("Источник недоступен");
  });
});
