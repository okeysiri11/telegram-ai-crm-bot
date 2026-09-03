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
import { formatFxQuote, fxWatchlistQuoteRow } from "./fxQuoteDisplay";
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
    expect(integrityLabel("live", 1.1)).toBeNull();
    expect(integrityLabel("delayed", 1.1)).toBeNull();
    expect(integrityLabel("connected")).toBe("Нет данных");
    expect(integrityLabel("connected", Number.NaN)).toBe("Нет данных");
    expect(integrityLabel("not_connected")).toBe("Источник недоступен");
    expect(integrityLabel("insufficient_data")).toBe("Данные неполные");
  });

  it("formatFxQuote never emits NaN", () => {
    expect(formatFxQuote(1.08512, 4)).toBe("1.0851");
    expect(formatFxQuote("99.87", 3)).toBe("99.870");
    expect(formatFxQuote(Number.NaN)).toBeNull();
    expect(formatFxQuote("NaN")).toBeNull();
    expect(formatFxQuote("—")).toBeNull();
  });

  it("DXY watchlist row uses live quote mid instead of a hardcoded dash", () => {
    const row = fxWatchlistQuoteRow(
      "DXY",
      { mid: 99.87, bid: 99.86, ask: 99.88, fetched_at: "2026-09-02T12:00:00Z", source: "Yahoo Finance (DX-Y.NYB)" },
      3,
    );
    expect(row.bid).toBe("99.860");
    expect(row.ask).toBe("99.880");
    expect(row.updated).not.toBe("нет данных");
    expect(row.source).toContain("Yahoo");
  });

  it("russian analysis preset names", () => {
    expect(defaultAnalyses()[0].name.length).toBeGreaterThan(3);
  });
});
