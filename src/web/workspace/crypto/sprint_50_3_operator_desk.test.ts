import { beforeEach, describe, expect, it } from "vitest";
import {
  defaultAnalyses,
  defaultSpecialists,
  loadAgentSettings,
  loadChartInstrumentPrefs,
  loadWatchlist,
  saveAgentSettings,
  saveChartInstrumentPrefs,
  saveWatchlist,
} from "./otcPrefs";
import { integrityLabel } from "./paperTradingPanels";
import { CAL_FILTERS } from "./operatorCalendar";
import { tvSymbolFor } from "./TradingViewEmbed";

describe("sprint 50.3 operator desk", () => {
  beforeEach(() => localStorage.clear());

  it("vertical dual-chart TV symbols", () => {
    expect(tvSymbolFor("EUR/USD")).toBe("FX:EURUSD");
    expect(tvSymbolFor("DXY")).toBe("TVC:DXY");
  });

  it("independent timeframe persistence for primary/comparison", () => {
    saveChartInstrumentPrefs(
      { primary: "EUR/USD", comparison: "DXY", eurusdTf: "15m", dxyTf: "4h" },
      "t1",
    );
    const p = loadChartInstrumentPrefs("t1");
    expect(p.primary).toBe("EUR/USD");
    expect(p.comparison).toBe("DXY");
    expect(p.eurusdTf).toBe("15m");
    expect(p.dxyTf).toBe("4h");
  });

  it("my instruments watchlist persistence", () => {
    saveWatchlist(["EUR/USD", "DXY"], "t1");
    expect(loadWatchlist("t1")).toEqual(["EUR/USD", "DXY"]);
  });

  it("analysis Run Now presets and settings", () => {
    const ids = defaultAnalyses().map((a) => a.id);
    expect(ids).toEqual(expect.arrayContaining(["morning", "evening", "pre_trade", "event"]));
    expect(defaultAnalyses().every((a) => a.name.length > 2)).toBe(true);
  });

  it("specialist Run Now and settings", () => {
    const specs = defaultSpecialists();
    expect(specs.map((s) => s.id)).toEqual(
      expect.arrayContaining(["chief", "technical", "macro", "news"]),
    );
    saveAgentSettings({ chief: { enabled: true, weight: 1.5, instruments: ["EUR/USD", "DXY"] } }, "t1");
    expect(loadAgentSettings("t1").chief.weight).toBe(1.5);
  });

  it("calendar filters cover russian categories", () => {
    const labels = CAL_FILTERS.map((f) => f.label);
    expect(labels).toEqual(
      expect.arrayContaining([
        "Макроэкономика",
        "Новости",
        "Анализы",
        "AI-специалисты",
        "Сигналы",
        "Сессии",
        "Paper Trading",
      ]),
    );
  });

  it("russian integrity / honesty labels", () => {
    expect(integrityLabel("error")).toBe("Источник недоступен");
    expect(integrityLabel("connected", 1.1)).toBeNull();
    expect(integrityLabel("connected")).toBe("Нет данных");
    expect(integrityLabel("stale")).toBe("Данные устарели");
    expect(integrityLabel("partial")).toBe("Частичные данные");
    expect(integrityLabel("needs_config")).toBe("Источник недоступен");
  });

  it("cross-link russian UI names allowed", () => {
    expect(["EUR/USD", "DXY", "TradingView", "Technical Agent", "Macro Agent", "News Agent"]).toContain(
      "EUR/USD",
    );
    expect(defaultSpecialists().find((s) => s.id === "technical")?.name).toBe("Technical Agent");
  });
});
