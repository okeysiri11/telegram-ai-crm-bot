import { describe, expect, it } from "vitest";
import { normalizeSymbolClient } from "./symbolNormalize";
import { tvSymbolFor } from "./TradingViewEmbed";
import { defaultAnalyses, loadWatchlist } from "./otcPrefs";

describe("sprint 50.1 fx live desk", () => {
  it("normalizes EURUSD and DXY", () => {
    expect(normalizeSymbolClient("EURUSD")).toBe("EUR/USD");
    expect(normalizeSymbolClient("USDX")).toBe("DXY");
  });

  it("maps TradingView symbols without credentials", () => {
    expect(tvSymbolFor("EUR/USD")).toBe("FX:EURUSD");
    expect(tvSymbolFor("DXY")).toBe("TVC:DXY");
  });

  it("defaults watchlist to EUR/USD + DXY", () => {
    // jsdom localStorage empty
    expect(loadWatchlist()).toEqual(["EUR/USD", "DXY"]);
  });

  it("includes morning and session analysis presets", () => {
    const ids = defaultAnalyses().map((a) => a.id);
    expect(ids).toContain("morning");
    expect(ids).toContain("pre_europe");
    expect(ids).toContain("pre_us");
    expect(ids).toContain("evening");
  });
});
