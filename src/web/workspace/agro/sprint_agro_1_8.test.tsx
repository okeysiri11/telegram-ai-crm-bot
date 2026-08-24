/**
 * AGRO 1.8 — health colors, gap severity, lineage, refresh vs recalculate.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";

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
            freshness: [{ provider_id: "weather_provider", label_ru: "Open-Meteo", age_ru: "менее часа" }],
            gaps: ["Нет официальных ценовых рядов."],
            gaps_structured: [
              { severity: "CRITICAL", text: "Нет официальных ценовых рядов.", code: "all_prices" },
              { severity: "OPTIONAL", text: "Резервный погодный провайдер не настроен.", code: "secondary_weather" },
            ],
            series: { price: [], production: [], yield_or_area: [], trade: [], fx: [], weather: [] },
          },
        };
      }
      if (path.includes("/scheduler")) {
        return {
          ok: true,
          status: 200,
          json: {
            timezone: "Europe/Kyiv",
            jobs: [{ id: "ops_refresh", cron_kyiv: "45 5 * * *", label_ru: "Обновление погоды / FX / операционка" }],
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
                health_color: "green",
                last_success_at: "2026-08-17T12:00:00+00:00",
                numeric_count: 12,
                observation_count: 12,
                data_type_ru: "Числовой ряд",
                market_usable: true,
              },
              {
                id: "ua_agro_ministry",
                label_ru: "Минагрополитики",
                health_state: "BLOCKED",
                health_color: "red",
                observation_count: 0,
              },
            ],
          },
        };
      }
      if (path.includes("/reports") || path.includes("/agents") || path.includes("/analytics")) {
        return { ok: true, status: 200, json: { ok: true, items: [] } };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" }, source_class: "UNKNOWN" } })),
  };
});

describe("AGRO 1.8 health colors and actions", () => {
  it("colors CONNECTED green and BLOCKED red", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const green = await screen.findByTestId("agro-health-weather_provider");
    expect(green.getAttribute("data-health-color")).toBe("green");
    const red = screen.getByTestId("agro-health-ua_agro_ministry");
    expect(red.getAttribute("data-health-color")).toBe("red");
  });

  it("groups gaps by severity and has refresh vs recalculate", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const gaps = await screen.findByTestId("agro-intel-gaps");
    expect(gaps.textContent).toMatch(/Критичный/);
    expect(gaps.textContent).toMatch(/Опциональный/);
    expect(screen.getByText("Обновить все")).toBeTruthy();
    expect(screen.getByText("Пересчитать анализ")).toBeTruthy();
  });

  it("shows add-url and kyiv scheduler", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    expect(await screen.findByText("Добавить URL")).toBeTruthy();
    fireEvent.click(screen.getByText("Доверие HIGH"));
    const sched = await screen.findByTestId("agro-intel-scheduler");
    expect(sched.textContent).toMatch(/45 5/);
    expect(sched.textContent).toMatch(/Europe\/Kyiv|Обновление погоды/);
  });

  it("analytics lineage control is present", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    expect(await screen.findByText("Пересчитать анализ")).toBeTruthy();
    expect((await screen.findByTestId("agro-analytics-gaps")).textContent).toMatch(/Критичный/);
  });
});
