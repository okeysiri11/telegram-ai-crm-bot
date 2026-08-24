/**
 * AGRO 2.0 — weather map, history open, source actions, settings IA, business UI.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";
import { AgroSettingsPanel } from "./AgroSettingsPanel";
import { AgroWeatherPanel } from "./AgroWeatherPanel";

const odesaDrawer = {
  ok: true,
  item: { id: "odesa", label_ru: "Одесская область", temperature: 35, rain: 1, missing: false, tmax_avg: 34.5, precip_7: 1.5 },
  forecast_7: [{ date: "2026-08-18", tmax: 35, precip: 1 }],
  monthly_outlook_ru: "Недостаточно данных для сравнения с климатической нормой.",
  risk: { level: "High", label_ru: "Высокий риск дефицита влаги", explanation_ru: "Жара и мало осадков." },
  crop_impact: [{ crop_id: "corn", crop_ru: "Кукуруза", level: "High", explanation_ru: "стресс" }],
};

const lvivDrawer = {
  ok: true,
  item: { id: "lviv", label_ru: "Львовская область", temperature: 18, rain: 12, missing: false, tmax_avg: 18.2, precip_7: 45 },
  forecast_7: [{ date: "2026-08-18", tmax: 18, precip: 12 }],
  monthly_outlook_ru: "Недостаточно данных для сравнения с климатической нормой.",
  risk: { level: "High", label_ru: "Высокий риск избытка влаги", explanation_ru: "Много осадков." },
  crop_impact: [{ crop_id: "wheat", crop_ru: "Пшеница", level: "High", explanation_ru: "избыток влаги" }],
};

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.includes("/weather/regions/odesa")) {
        return { ok: true, status: 200, json: odesaDrawer };
      }
      if (path.includes("/weather/regions/lviv")) {
        return { ok: true, status: 200, json: lvivDrawer };
      }
      if (path.includes("/weather/dashboard")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            macros: [
              {
                macro_id: "south",
                title_ru: "ЮГ УКРАИНЫ",
                next_7_ru: "сухая и жаркая погода.",
                month_ru: "Недостаточно данных для сравнения с климатической нормой.",
                risk_ru: "повышенный риск дефицита влаги.",
                impact_ru: "кукуруза и подсолнечник могут испытывать стресс.",
                monitor_ru: "осадки, температуру почвы, состояние посевов.",
              },
            ],
            oblasts: [
              { id: "odesa", label_ru: "Одесская область", lat: 46.48, lon: 30.73, x: 380, y: 350, has_data: true, macro: "south" },
              { id: "lviv", label_ru: "Львовская область", lat: 49.84, lon: 24.03, x: 90, y: 150, has_data: true, macro: "west" },
            ],
            map: {
              regions: [
                { id: "odesa", label_ru: "Одесская область", lat: 46.48, lon: 30.73, x: 380, y: 350, has_data: true },
                { id: "lviv", label_ru: "Львовская область", lat: 49.84, lon: 24.03, x: 90, y: 150, has_data: true },
              ],
            },
            crops: [
              {
                id: "wheat",
                label_ru: "Пшеница",
                regions: [
                  { macro_id: "south", short_ru: "Юг", level: "Medium", label_ru: "Средний риск", explanation_ru: "Юг пшеница" },
                  { macro_id: "west", short_ru: "Запад", level: "High", label_ru: "Высокий риск избытка влаги", explanation_ru: "Запад пшеница" },
                ],
              },
            ],
            matrix: {
              columns: [
                { id: "wheat", label_ru: "Пшеница", label_en: "Wheat" },
                { id: "corn", label_ru: "Кукуруза", label_en: "Corn" },
                { id: "sunflower", label_ru: "Подсолнечник", label_en: "Sunflower" },
                { id: "barley", label_ru: "Ячмень", label_en: "Barley" },
                { id: "soy", label_ru: "Соя", label_en: "Soy" },
              ],
              rows: [
                { macro_id: "south", label_ru: "Юг", label_en: "South", cells: { wheat: { level: "Medium", label_en: "Medium", label_ru: "Средний риск", explanation_ru: "cell south wheat" } } },
              ],
            },
            history: {
              today: { ok: true },
              days_7: { precip: 12, text_ru: null },
              days_30: { text_ru: "Недостаточно данных для сравнения с климатической нормой." },
              season: { text_ru: "Недостаточно данных для сравнения с климатической нормой." },
              note_ru: "Недостаточно данных для сравнения с климатической нормой.",
            },
            provider: { id: "weather_provider", label_ru: "Open-Meteo", health_state: "CONNECTED" },
          },
        };
      }
      if (path.includes("/settings/desk")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            tabs: [
              { id: "general", label_ru: "ОБЩИЕ" },
              { id: "diagnostics", label_ru: "ДИАГНОСТИКА" },
            ],
            item: {
              analytics_detail: "standard",
              morning_report_enabled: true,
              evening_report_enabled: true,
              crop_impact_enabled: true,
              specialists: { ukraine: true },
            },
            specialist_catalog: [{ id: "ukraine", label_en: "Ukraine", enabled: true }],
            schedule: [{ id: "ops_refresh", time_kyiv: "05:45", label_ru: "Обновление данных", when_ru: "ежедневно", cron_kyiv: "45 5 * * *" }],
            diagnostics: [{ provider_id: "ua_agro_ministry", label_ru: "Минагрополитики", http_status: 403, error: "HTTP 403", health_state: "BLOCKED" }],
            pipeline_version: "AGRO_1_9",
            ux_version: "AGRO_2_0",
          },
        };
      }
      if (path.includes("/analytics/an-20")) {
        return {
          ok: true,
          status: 200,
          json: {
            item: {
              id: "an-20",
              analysis_type: "operational",
              title_ru: "Оперативный анализ",
              chief: { bias: "WATCH", confidence: 50, note_ru: "Следить" },
              sections: {},
              sources: [{ provider_id: "weather_provider", records: [{ id: "o1", text: "Open-Meteo tmax" }] }],
            },
          },
        };
      }
      if (path.includes("/analytics/dashboard")) {
        return {
          ok: true,
          status: 200,
          json: {
            business_brief: { text_ru: "Получены свежие данные по погоде, валюте, торговле и рынкам." },
            risk_cards: [{ title_ru: "Погода", severity: "HIGH", summary_ru: "Жара на юге", why_ru: "Open-Meteo", monitor_ru: "осадки" }],
            opportunity_cards: [{ commodity: "Пшеница", reason_ru: "Спред", region: "Одесса" }],
            what_changed: [{ text_ru: "UAH: -0.4%" }],
            coverage: { connected_sources: 4, numeric_observations: 10, metadata_observations: 2, observations_last_24h: 3, coverage_pct: 80, confidence_pct: 70, unresolved_gaps: 1 },
            source_health: { healthy: 3, partial: 1, needs_key: 0, optional: 1, failed: 0 },
            operational_counts: { numeric_observations: 10, fresh_24h: 3, last_7d: 6, historical: 1, price: 2, weather: 4, trade: 2, logistics: 1 },
            series: { price: [], production: [], yield_or_area: [], trade: [], fx: [], weather: [] },
            freshness: [],
            gaps: [],
            gaps_structured: [],
          },
        };
      }
      if (path === "/analytics" || path.endsWith("/analytics")) {
        return {
          ok: true,
          status: 200,
          json: {
            items: [
              { id: "an-20", analysis_type: "operational", generated_at_human: "18 августа", topic_ru: "Общий рынок", bias: "WATCH", confidence: 50, sources_count: 3 },
              { id: "an-21", analysis_type: "morning", generated_at_human: "18 августа", topic_ru: "Общий рынок", bias: "WATCH", confidence: 40, sources_count: 2 },
            ],
          },
        };
      }
      if (path.includes("/scheduler")) {
        return {
          ok: true,
          status: 200,
          json: {
            jobs: [{ id: "ops_refresh", cron_kyiv: "45 5 * * *", label_ru: "Обновление данных" }],
            jobs_human: [{ id: "ops_refresh", time_kyiv: "05:45", label_ru: "Обновление данных", cron_kyiv: "45 5 * * *" }],
          },
        };
      }
      if (path.includes("/providers/weather_provider")) {
        return {
          ok: true,
          status: 200,
          json: { ok: true, item: { id: "weather_provider", label_ru: "Open-Meteo", url: "https://api.open-meteo.com", health_state: "CONNECTED" }, observations: [{ id: "w1", title: "Kyiv Tmax 24", published_at: "2026-08-18" }] },
        };
      }
      if (path.includes("/providers")) {
        return {
          ok: true,
          status: 200,
          json: {
            items: [
              {
                id: "weather_provider",
                label_ru: "Open-Meteo",
                health_state: "CONNECTED",
                health_color: "green",
                url: "https://api.open-meteo.com/v1/forecast",
                observation_count: 8,
                error: "HTTP 403",
                note_ru: "HTTP 403 metadata_only pipeline_version",
              },
              {
                id: "fx_rates",
                label_ru: "НБУ",
                health_state: "CONNECTED",
                url: "https://bank.gov.ua/",
                observation_count: 4,
              },
            ],
          },
        };
      }
      if (path.includes("/reports") || path.includes("/agents")) {
        return { ok: true, status: 200, json: { items: [] } };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 200, json: { ok: true, item: { note_ru: "Проверка завершена" } } })),
    agroOpsPut: vi.fn(async () => ({ ok: true, status: 200, json: { ok: true, item: { report_length: "short" } } })),
  };
});

describe("AGRO 2.0 weather map and crop impact", () => {
  it("renders Ukraine map and opens different oblast data", async () => {
    render(<AgroWeatherPanel headers={{}} />);
    expect(await screen.findByTestId("agro-weather-map")).toBeTruthy();
    fireEvent.click(screen.getByTestId("agro-weather-oblast-odesa"));
    const drawer = await screen.findByTestId("agro-weather-drawer");
    expect(drawer.textContent).toMatch(/35/);
    expect(screen.getByTestId("agro-weather-crop-impact").textContent).toMatch(/Кукуруза/);
    fireEvent.click(screen.getByTestId("agro-weather-oblast-lviv"));
    const again = await screen.findByTestId("agro-weather-drawer");
    expect(again.textContent).toMatch(/18/);
    expect(again.textContent).not.toMatch(/35 °C/);
  });

  it("shows crop-weather, matrix and climate-normal honesty", async () => {
    render(<AgroWeatherPanel headers={{}} />);
    expect((await screen.findByTestId("agro-weather-crops")).textContent).toMatch(/ПШЕНИЦА/);
    fireEvent.click(screen.getByText(/Юг: Средний риск/));
    expect((await screen.findByTestId("agro-weather-crop-explain")).textContent).toMatch(/Юг пшеница/);
    fireEvent.click(screen.getByText("Средний риск"));
    expect((await screen.findByTestId("agro-weather-matrix-explain")).textContent).toMatch(/cell south wheat/);
    fireEvent.click(within(screen.getByTestId("agro-weather-history")).getByText("30 дней"));
    expect(screen.getByTestId("agro-weather-history").parentElement?.textContent).toMatch(/климатической нормой/);
  });
});

describe("AGRO 2.0 history and source actions", () => {
  it("opens every analytics history item", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    await screen.findByTestId("agro-analytics-history");
    fireEvent.click(screen.getByTestId("agro-analytics-open-an-20"));
    expect(await screen.findByTestId("agro-analytics-chief")).toBeTruthy();
    fireEvent.click(screen.getByTestId("agro-analytics-open-an-21"));
    const { agroOpsGet } = await import("../business-ops/opsApi");
    expect(vi.mocked(agroOpsGet).mock.calls.some((c) => String(c[0]).includes("/analytics/an-21"))).toBe(true);
  });

  it("source probe latest open and settings work", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByTestId("agro-source-latest-weather_provider"));
    expect((await screen.findByTestId("agro-intel-source-drawer")).textContent).toMatch(/Kyiv Tmax/);
    fireEvent.click(screen.getByTestId("agro-source-settings-weather_provider"));
    expect(screen.getByText(/Настройки: Open-Meteo/)).toBeTruthy();
    expect(screen.getByTestId("agro-source-open-weather_provider").getAttribute("href")).toMatch(/open-meteo/);
    fireEvent.click(screen.getByTestId("agro-source-probe-weather_provider"));
    const { agroOpsPost } = await import("../business-ops/opsApi");
    expect(vi.mocked(agroOpsPost).mock.calls.some((c) => String(c[0]).includes("/providers/weather_provider/probe"))).toBe(true);
  });

  it("hides raw HTTP errors from business intel UI", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const panel = await screen.findByTestId("agro-intel-panel");
    expect(screen.queryByText(/HTTP 403/)).toBeNull();
    expect(screen.queryByText(/pipeline_version/)).toBeNull();
    expect(panel.textContent).toMatch(/Получены свежие данные|Свежих рыночных рядов/);
    expect(screen.getByTestId("agro-intel-scheduler").textContent).toMatch(/05:45/);
    expect(screen.getByTestId("agro-intel-scheduler").textContent).toMatch(/45 5/);
  });
});

describe("AGRO 2.0 settings IA", () => {
  it("navigates tabs and keeps diagnostics with HTTP details", async () => {
    render(
      <AgroSettingsPanel
        headers={{}}
        roleLabel="Директор"
        agroRole="agro_director"
        canAdmin
        providers={[{ id: "weather_provider", label_ru: "Open-Meteo", status: "CONNECTED" }]}
        channels={{ telegram: { id: "telegram", connected: false, label_ru: "Telegram — не настроен" } }}
      />,
    );
    expect(await screen.findByTestId("agro-settings-tabs")).toBeTruthy();
    fireEvent.click(screen.getByText("АГРОРАЗВЕДКА"));
    expect(screen.getByTestId("agro-settings-intel")).toBeTruthy();
    fireEvent.click(screen.getByText("АНАЛИТИКА"));
    expect(screen.getByTestId("agro-settings-analytics").textContent).toMatch(/Стандартно/);
    fireEvent.click(screen.getByText("ПОГОДА"));
    expect(screen.getByTestId("agro-settings-weather")).toBeTruthy();
    fireEvent.click(screen.getByText("РАСПИСАНИЕ"));
    expect(screen.getByTestId("agro-settings-schedule").textContent).toMatch(/05:45/);
    fireEvent.click(screen.getByText("Расширенные настройки"));
    expect(screen.getByTestId("agro-settings-schedule-cron").textContent).toMatch(/45 5/);
    fireEvent.click(screen.getByText("ДИАГНОСТИКА"));
    expect(screen.getByTestId("agro-settings-diagnostics").textContent).toMatch(/HTTP 403/);
  });
});
