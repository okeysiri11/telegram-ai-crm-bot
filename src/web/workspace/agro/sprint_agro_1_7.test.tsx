/**
 * AGRO 1.7 — coverage card, Open-Meteo freshness, visible DEMO.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";
import { AgroCoverageCard } from "./AgroCoverageCard";

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
            coverage: {
              connected_sources: 6,
              numeric_observations: 128,
              metadata_observations: 40,
              observations_last_24h: 14,
              coverage_pct: 100,
              confidence_pct: 96,
              unresolved_gaps: 4,
            },
            freshness: [{ provider_id: "weather_provider", label_ru: "Open-Meteo", age_ru: "менее часа" }],
            gaps: ["FAOSTAT QCL (производство пшеницы Украины, тонны): fenixservices.fao.org timeout / HTTP 521."],
            series: {
              price: [{ t: "2024-07", v: 126.2, unit: "index", source: "fao" }],
              production: [{ t: "2024", v: 1, unit: "t", source: "eurostat" }],
              yield_or_area: [],
              trade: [{ t: "2024", v: 36, unit: "USD", source: "world_bank" }],
              fx: [{ t: "2026-08-17", v: 41.2, unit: "UAH", source: "fx_rates" }],
              weather: [
                { t: "2026-08-16", v: 24, unit: "°C", source: "weather_provider" },
                { t: "2026-08-17", v: 26, unit: "°C", source: "weather_provider" },
              ],
            },
          },
        };
      }
      if (path.includes("/providers")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            items: [
              {
                id: "weather_provider",
                label_ru: "Open-Meteo (Киев)",
                health_state: "CONNECTED",
                last_success_at: "2026-08-17T12:00:00+00:00",
                numeric_count: 12,
                observation_count: 12,
                data_type_ru: "Числовой ряд",
                market_usable: true,
              },
            ],
          },
        };
      }
      if (path.includes("/reports")) {
        return {
          ok: true,
          status: 200,
          json: { ok: true, items: [{ id: "r1", title: "Утренний обзор", sources_count: 6, generated_at: "2026-08-17T12:00:00+00:00" }] },
        };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
  };
});

describe("AGRO 1.7 coverage and freshness", () => {
  it("coverage card prints required stats", () => {
    render(
      <AgroCoverageCard
        coverage={{
          connected_sources: 6,
          numeric_observations: 128,
          metadata_observations: 40,
          observations_last_24h: 14,
          coverage_pct: 100,
          confidence_pct: 96,
          unresolved_gaps: 4,
        }}
      />,
    );
    const card = screen.getByTestId("agro-coverage-card");
    expect(card.textContent).toMatch(/Источников подключено: 6/);
    expect(card.textContent).toMatch(/Реальных наблюдений: 128/);
    expect(card.textContent).toMatch(/Метаданных: 40/);
    expect(card.textContent).toMatch(/Данные за последние 24 часа: 14/);
    expect(card.textContent).toMatch(/Coverage:/);
    expect(card.textContent).toMatch(/100%/);
    expect(card.textContent).toMatch(/Confidence:/);
    expect(card.textContent).toMatch(/96%/);
    expect(card.textContent).toMatch(/Unresolved gaps:/);
    expect(card.textContent).toMatch(/4/);
  });

  it("intel freshness does not say нет данных for Open-Meteo", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const fresh = await screen.findByTestId("agro-intel-freshness");
    expect(fresh.textContent).toMatch(/Open-Meteo/);
    expect(fresh.textContent).not.toMatch(/Open-Meteo: нет данных/);
    expect(await screen.findByTestId("agro-coverage-card")).toBeTruthy();
  });

  it("analytics coverage card is present", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    expect(await screen.findByTestId("agro-coverage-card")).toBeTruthy();
    expect((await screen.findByTestId("agro-coverage-card")).textContent).toMatch(/Источников подключено: 6/);
  });
});
