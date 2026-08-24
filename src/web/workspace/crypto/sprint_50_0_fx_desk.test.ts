/**
 * Sprint 50.0 — EUR/USD + DXY desk defaults and no fabricated quotes in UI prefs.
 */

import { describe, expect, it, beforeEach } from "vitest";
import { loadWatchlist, saveWatchlist, defaultAnalyses, defaultSpecialists } from "../crypto/otcPrefs";
import { NullChartProvider } from "../crypto/chartProvider";
import { normalizeSymbolClient } from "../crypto/symbolNormalize";

describe("Sprint 50.0 crypto FX desk", () => {
  beforeEach(() => localStorage.clear());

  it("defaults watchlist to EUR/USD and DXY with tenant isolation", () => {
    expect(loadWatchlist()).toEqual(["EUR/USD", "DXY"]);
    saveWatchlist(["EUR/USD"], "tenant-a");
    saveWatchlist(["DXY"], "tenant-b");
    expect(loadWatchlist("tenant-a")).toEqual(["EUR/USD"]);
    expect(loadWatchlist("tenant-b")).toEqual(["DXY"]);
  });

  it("analysis presets include morning/pre-trade/event/evening with EUR/USD+DXY", () => {
    const ids = defaultAnalyses().map((a) => a.id);
    expect(ids).toEqual(expect.arrayContaining(["morning", "pre_trade", "event", "evening"]));
    for (const a of defaultAnalyses()) {
      expect(a.instruments).toEqual(expect.arrayContaining(["EUR/USD", "DXY"]));
      expect(a.status).toBeTruthy();
    }
  });

  it("specialists include Chief and DXY analyst", () => {
    const names = defaultSpecialists().map((s) => s.name);
    expect(names).toEqual(
      expect.arrayContaining(["EUR/USD Structure Agent", "DXY Agent", "Chief Analyst"]),
    );
  });

  it("chart provider does not fabricate quotes when disconnected", async () => {
    const snap = await new NullChartProvider().loadChart("EUR/USD", "1h");
    expect(snap.quote).toBeNull();
    expect(snap.status).toBe("not_connected");
  });

  it("normalizes EURUSD aliases on client", () => {
    expect(normalizeSymbolClient("EURUSD")).toBe("EUR/USD");
    expect(normalizeSymbolClient("dxy")).toBe("DXY");
  });
});
