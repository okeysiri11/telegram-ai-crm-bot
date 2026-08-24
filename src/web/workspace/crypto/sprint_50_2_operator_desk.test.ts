import { beforeEach, describe, expect, it } from "vitest";
import {
  defaultAnalyses,
  defaultSpecialists,
  loadAgentSettings,
  loadWatchlist,
  saveAgentSettings,
  saveWatchlist,
} from "./otcPrefs";
import { integrityLabel } from "./paperTradingPanels";
import { tvSymbolFor } from "./TradingViewEmbed";

describe("sprint 50.2 operator desk", () => {
  beforeEach(() => localStorage.clear());

  it("dual instrument TV symbols", () => {
    expect(tvSymbolFor("EUR/USD")).toBe("FX:EURUSD");
    expect(tvSymbolFor("DXY")).toBe("TVC:DXY");
  });

  it("watchlist persistence", () => {
    saveWatchlist(["EUR/USD", "DXY", "GBP/USD"], "t1");
    expect(loadWatchlist("t1")).toEqual(["EUR/USD", "DXY", "GBP/USD"]);
  });

  it("analysis and specialist presets exist for Run Now", () => {
    expect(defaultAnalyses().map((a) => a.id)).toEqual(expect.arrayContaining(["morning", "evening"]));
    expect(defaultSpecialists().map((s) => s.id)).toEqual(
      expect.arrayContaining(["chief", "technical", "macro", "news"]),
    );
  });

  it("agent settings persistence", () => {
    saveAgentSettings({ technical: { enabled: true, weight: 1.2, instruments: ["EUR/USD"] } }, "t1");
    expect(loadAgentSettings("t1").technical.weight).toBe(1.2);
  });

  it("russian integrity labels", () => {
    expect(integrityLabel("error")).toBe("Источник недоступен");
    expect(integrityLabel("connected", 1.1)).toBeNull();
    expect(integrityLabel("connected")).toBe("Нет данных");
    expect(integrityLabel("not_connected")).toBe("Источник недоступен");
    expect(integrityLabel("insufficient_data")).toBe("Данные неполные");
  });

  it("russian analysis preset names", () => {
    expect(defaultAnalyses()[0].name.length).toBeGreaterThan(3);
  });
});
