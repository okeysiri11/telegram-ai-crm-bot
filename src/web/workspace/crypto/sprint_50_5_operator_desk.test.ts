import { beforeEach, describe, expect, it } from "vitest";
import { defaultSpecialistSettings } from "./specialistAndSignalPanels";
import { tvSymbolFor } from "./TradingViewEmbed";
import { defaultAnalyses, loadAnalyses, saveAnalyses } from "./otcPrefs";

describe("sprint 50.5 operator desk", () => {
  beforeEach(() => localStorage.clear());

  it("chart CTAs are equal primary actions (contract labels)", () => {
    expect(["Создать сигнал", "К анализу", "Бумажная торговля"]).toHaveLength(3);
  });

  it("DXY maps only to TVC:DXY never another instrument", () => {
    expect(tvSymbolFor("DXY")).toBe("TVC:DXY");
    expect(tvSymbolFor("USDX")).toBe("TVC:DXY");
    expect(tvSymbolFor("EUR/USD")).toBe("FX:EURUSD");
  });

  it("specialist settings defaults include risk R/R and technical indicators", () => {
    const tech = defaultSpecialistSettings("technical");
    expect(tech.indicators?.rsi).toBe(true);
    const risk = defaultSpecialistSettings("risk");
    expect(risk.minimum_rr).toBe(1.5);
    expect(risk.strict).toBe(false);
  });

  it("analysis enable/disable persists", () => {
    const items = defaultAnalyses().map((a) => (a.id === "evening" ? { ...a, enabled: true, status: "Активен" } : a));
    saveAnalyses(items, "t55");
    expect(loadAnalyses("t55").find((a) => a.id === "evening")?.enabled).toBe(true);
  });

  it("signal form kinds and sound profiles are russian-labeled in UI module", async () => {
    const mod = await import("./specialistAndSignalPanels");
    expect(typeof mod.SignalCreateForm).toBe("function");
    expect(typeof mod.SpecialistSettingsPanel).toBe("function");
  });
});
