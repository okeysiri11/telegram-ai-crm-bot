/**
 * AGRO 1.9 — source health, operational counts, quality, stale reports, charts.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";
import { AgroMarketsPanel } from "./AgroMarketsPanel";

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.includes("/analytics/dashboard")) {
        return {
          ok: true,
          status: 200,
          json: {
            coverage: { connected_sources: 6, numeric_observations: 20, metadata_observations: 4, observations_last_24h: 8, coverage_pct: 100, confidence_pct: 90, unresolved_gaps: 2 },
            source_health: { healthy: 4, partial: 2, needs_key: 1, optional: 3, failed: 1, last_full_refresh_at: "2026-08-18T06:00:00+00:00", refresh_duration_sec: 11 },
            operational_counts: { numeric_observations: 20, fresh_24h: 8, last_7d: 12, historical: 8, price: 5, weather: 6, trade: 4, logistics: 2 },
            quality_flags: [{ code: "stale", text: "Свежий операционный ряд устарел (>72ч).", kept: true, severity: "IMPORTANT" }],
            anomalies: [{ text: "ANOMALY: price wheat изменение 12% на 4 сопоставимых точках." }],
            freshness: [{ provider_id: "weather_provider", label_ru: "Open-Meteo", age_ru: "менее часа" }],
            gaps: [],
            gaps_structured: [],
            series: {
              price: [{ t: "2026-08-01", v: 100, unit: "EUR/t", metric: "wheat" }, { t: "2026-08-02", v: 110, unit: "EUR/t", metric: "wheat" }],
              production: [],
              yield_or_area: [],
              trade: [],
              fx: [],
              weather: [{ t: "2026-08-01", v: 28, unit: "°C", metric: "tmax" }, { t: "2026-08-02", v: 30, unit: "°C", metric: "tmax" }],
            },
          },
        };
      }
      if (path.includes("/scheduler")) {
        return { ok: true, status: 200, json: { timezone: "Europe/Kyiv", jobs: [] } };
      }
      if (path.includes("/providers")) {
        return { ok: true, status: 200, json: { ok: true, items: [] } };
      }
      if (path.includes("/reports")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            items: [
              { id: "new", title: "Утренний обзор", report_date: "2026-08-18", is_latest: true, latest_badge_ru: "АКТУАЛЬНЫЙ", sources_count: 5, confidence: 72 },
              { id: "old", title: "Утренний обзор v1", report_date: "2026-08-18", is_latest: false, latest_badge_ru: "УСТАРЕЛ", sources_count: 5, confidence: 40 },
            ],
          },
        };
      }
      if (path.includes("/markets/dashboard")) {
        return {
          ok: true,
          status: 200,
          json: {
            current: [{ id: "q1", market_name: "Одесса", price: 42, currency: "USD", source_type: "MANUAL", manual_status: "CONFIRMED" }],
          },
        };
      }
      if (path.includes("/agents") || path.includes("/analytics")) {
        return { ok: true, status: 200, json: { ok: true, items: [] } };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
  };
});

describe("AGRO 1.9 health counts quality reports", () => {
  it("shows source health and operational numeric counts", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const health = await screen.findByTestId("agro-source-health");
    expect(health.textContent).toMatch(/Healthy:\s*4/);
    expect(health.textContent).toMatch(/Partial:\s*2/);
    expect(health.textContent).toMatch(/Needs key:\s*1/);
    expect(health.textContent).toMatch(/Failed:\s*1/);
    expect(health.textContent).toMatch(/Refresh duration/);
    const counts = screen.getByTestId("agro-operational-counts");
    expect(counts.textContent).toMatch(/Числовых наблюдений:\s*20/);
    expect(counts.textContent).toMatch(/Логистических:\s*2/);
    expect(screen.getByTestId("agro-quality-flags").textContent).toMatch(/сохранено/);
    expect(screen.getByTestId("agro-anomalies").textContent).toMatch(/ANOMALY/);
  });

  it("labels current vs stale reports correctly", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const hist = await screen.findByTestId("agro-intel-history");
    expect(hist.textContent).toMatch(/АКТУАЛЬНЫЙ/);
    expect(hist.textContent).toMatch(/УСТАРЕЛ/);
    expect(hist.textContent).not.toMatch(/v1 АКТУАЛЬНЫЙ/);
  });

  it("charts expose a single metric", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    const weather = await screen.findByTestId("agro-chart-weather");
    expect(weather.getAttribute("data-metric")).toBe("tmax");
    expect(weather.getAttribute("data-unit")).toBe("°C");
  });

  it("manual quotes show CONFIRMED trust", async () => {
    render(
      <AgroMarketsPanel
        headers={{}}
        canCreate
        canFinance
        markets={[{ id: "m1", name: "Одесса" }]}
        prices={[]}
        onChanged={() => undefined}
        onOpen={() => undefined}
        onAttach={() => undefined}
        onCreateCalc={() => undefined}
      />,
    );
    expect((await screen.findAllByTestId("agro-manual-trust"))[0].textContent).toBe("CONFIRMED");
    fireEvent.click(screen.getByText("Котировки"));
    expect(screen.getByTestId("agro-manual-status")).toBeTruthy();
  });
});
