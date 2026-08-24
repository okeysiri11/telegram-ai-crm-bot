/**
 * AGRO Weather Intelligence dashboard — map, tabs, crop, refresh, recs, errors.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { AgroWeatherPanel } from "./AgroWeatherPanel";

const dash = {
  ok: true,
  macros: [
    {
      macro_id: "south",
      title_ru: "ЮГ УКРАИНЫ",
      next_7_ru: "сухая и жаркая погода.",
      month_ru: "Недостаточно данных для сравнения с климатической нормой.",
      risk_ru: "повышенный риск дефицита влаги.",
      impact_ru: "кукуруза",
      monitor_ru: "осадки",
    },
  ],
  oblasts: [
    {
      id: "odesa",
      label_ru: "Одесская область",
      macro: "south",
      temperature: 35,
      rain: 1,
      precip_7: 1.5,
      humidity: 38,
      wind_speed: 7,
      agro_risk: { level: "High", label_ru: "Высокий" },
      missing: false,
      forecast_7: [{ date: "2026-08-18", tmax: 35, tmin: 22, precip: 1, precip_probability: 10, wind: 7 }],
    },
    {
      id: "lviv",
      label_ru: "Львовская область",
      macro: "west",
      temperature: 18,
      rain: 12,
      precip_7: 45,
      agro_risk: { level: "High", label_ru: "Высокий" },
      missing: false,
    },
  ],
  map: {
    regions: [
      { id: "odesa", label_ru: "Одесская область", has_data: true, temperature: 35, precip_7: 1.5, humidity: 38, wind_speed: 7, agro_risk: { level: "High", label_ru: "Высокий" } },
      { id: "lviv", label_ru: "Львовская область", has_data: true, temperature: 18, precip_7: 45, agro_risk: { level: "Medium", label_ru: "Умеренный" } },
    ],
  },
  crops: [
    {
      id: "wheat",
      label_ru: "Пшеница",
      regions: [{ macro_id: "south", short_ru: "Юг", level: "Medium", label_ru: "Средний риск", explanation_ru: "Юг пшеница" }],
    },
  ],
  matrix: {
    columns: [{ id: "wheat", label_ru: "Пшеница", label_en: "Wheat" }],
    rows: [{ macro_id: "south", label_ru: "Юг", label_en: "South", cells: { wheat: { level: "Medium", label_en: "Medium", label_ru: "Средний риск", explanation_ru: "cell" } } }],
  },
  history: {
    today: { ok: true },
    days_7: { precip: 12, text_ru: null },
    days_30: { text_ru: "Недостаточно данных для сравнения с климатической нормой." },
    season: { text_ru: "Недостаточно данных для сравнения с климатической нормой." },
    note_ru: "Недостаточно данных для сравнения с климатической нормой.",
  },
  region_cards: [
    { id: "south", title_ru: "ЮЖНЫЙ РЕГИОН", temperature: 26, feel_ru: "Жарко / сухо", precip_7: 2, humidity: 32, wind_speed: 7, agro_risk: { level: "High", label_ru: "Высокий" } },
    { id: "west", title_ru: "ЗАПАДНЫЙ РЕГИОН", temperature: 18, feel_ru: "Влажно", precip_7: 40, agro_risk: { level: "Medium", label_ru: "Умеренный" } },
  ],
  recommendations: [
    { id: "harvest", category_ru: "Сбор урожая", icon: "🌾", status: "favorable", status_ru: "Благоприятно", reason_ru: "Сухие дни", general: true, dates: ["2026-08-19"] },
    { id: "irrigation", category_ru: "Полив", icon: "💧", status: "recommended", status_ru: "Рекомендуется", reason_ru: "Низкая влажность", general: true },
  ],
  calendar: [{ id: "harvest", title_ru: "Сбор урожая", status_ru: "Благоприятно", status: "favorable", window_ru: "18–25 августа", reason_ru: "сухо" }],
  confidence: { score: 72, label_ru: "ВЫСОКИЙ", sources_count: 1, text_ru: "Прогноз основан на данных 1 источника" },
  last_updated: { display_ru: "18.08.2026 12:40" },
  outlook_30d: {
    temperature_trend: { text_ru: "Средняя максимальная температура по доступному прогнозу: 34°C. Сравнения с климатической нормой нет." },
    precipitation_trend: { text_ru: "Недостаточно данных для уверенного прогноза." },
    drought_probability: { text_ru: "повышенная вероятность" },
    agro_risk: { label_ru: "ВЫСОКИЙ" },
  },
  provider: { id: "weather_provider", label_ru: "Open-Meteo", health_state: "CONNECTED" },
};

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.includes("/crops/directory")) {
        return { ok: true, status: 200, json: { items: [{ name: "Пшеница" }, { name: "Кукуруза" }] } };
      }
      if (path.includes("/weather/regions/odesa") || path.includes("/weather/oblasts/odesa")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            item: { id: "odesa", label_ru: "Одесская область", temperature: 35, rain: 1, missing: false },
            forecast_7: [{ date: "2026-08-18", tmax: 35, precip: 1 }],
            monthly_outlook_ru: "Недостаточно данных для сравнения с климатической нормой.",
            risk: { level: "High", label_ru: "Высокий риск дефицита влаги" },
            crop_impact: [{ crop_id: "corn", crop_ru: "Кукуруза", level: "High", explanation_ru: "стресс" }],
            recommendations: [{ id: "irrigation", category_ru: "Полив", status_ru: "Рекомендуется", reason_ru: "сухо" }],
          },
        };
      }
      if (path.includes("/weather/forecast")) {
        return { ok: true, status: 200, json: { ok: true, forecast: [{ date: "2026-08-18", tmax: 26, precip: 2 }], item: { id: "south", label_ru: "ЮЖНЫЙ РЕГИОН", temperature: 26 } } };
      }
      if (path.includes("/weather/agro-risk")) {
        return { ok: true, status: 200, json: { agro_risk: { level: "High", label_ru: "Высокий" } } };
      }
      if (path.includes("/weather/recommendations")) {
        return { ok: true, status: 200, json: { recommendations: [{ id: "sowing", category_ru: "Посев", status_ru: "Высокий риск", reason_ru: "дефицит влаги" }] } };
      }
      if (path.includes("/weather/outlook")) {
        return { ok: true, status: 200, json: { monthly_outlook_ru: "Недостаточно данных для сравнения с климатической нормой.", outlook_30d: dash.outlook_30d } };
      }
      if (path.includes("/weather/overview") || path.includes("/weather/dashboard")) {
        return { ok: true, status: 200, json: dash };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async (path: string) => {
      if (path.includes("/weather/refresh")) {
        return { ok: true, status: 201, json: { ok: true, refreshed: 5, dashboard: dash } };
      }
      return { ok: true, status: 200, json: { ok: true } };
    }),
  };
});

describe("AGRO weather intelligence dashboard", () => {
  it("renders map, title, tabs and selects oblast", async () => {
    render(<AgroWeatherPanel headers={{}} />);
    expect(await screen.findByTestId("agro-weather-title")).toBeTruthy();
    expect(screen.getByTestId("agro-weather-map")).toBeTruthy();
    expect(screen.getByTestId("agro-weather-oblast-odesa")).toBeTruthy();
    expect(screen.getByTestId("agro-weather-region-label-odesa").textContent).toMatch(/Одесская/);
    expect(screen.getByTestId("agro-weather-capital-name-odesa").textContent).toBe("Одесса");
    expect(screen.getByTestId("agro-weather-region-label-kyiv").textContent).toMatch(/Киевская/);
    expect(screen.getByTestId("agro-weather-capital-name-kyiv").textContent).toBe("Киев");
    expect(screen.getByTestId("agro-weather-region-label-lviv").textContent).toMatch(/Львовская/);
    expect(screen.getByTestId("agro-weather-capital-name-lviv").textContent).toBe("Львов");
    expect(screen.getByTestId("agro-weather-capital-name-ivano_frankivsk").textContent).toBe("Ивано-Франковск");
    expect(screen.getByTestId("agro-weather-capital-name-kharkiv").textContent).toBe("Харьков");
    expect(screen.getByTestId("agro-weather-capital-name-dnipro").textContent).toBe("Днепр");
    expect(screen.getByTestId("agro-weather-capital-name-chernivtsi").textContent).toBe("Черновцы");
    expect(screen.getByTestId("agro-weather-capital-name-zakarpattia").textContent).toBe("Ужгород");
    fireEvent.click(within(screen.getByTestId("agro-weather-tabs")).getByText("7 дней"));
    expect(screen.getByTestId("agro-weather-forecast-grid")).toBeTruthy();
    fireEvent.click(within(screen.getByTestId("agro-weather-tabs")).getByText("Карта"));
    fireEvent.click(screen.getByTestId("agro-weather-oblast-odesa"));
    expect((await screen.findByTestId("agro-weather-drawer")).textContent).toMatch(/35/);
    fireEvent.click(screen.getByTestId("agro-weather-oblast-kharkiv"));
  });

  it("switches layers, crop, refresh, recommendations and region cards", async () => {
    render(<AgroWeatherPanel headers={{}} />);
    await screen.findByTestId("agro-weather-map");
    fireEvent.click(screen.getByText("Температура"));
    fireEvent.click(screen.getByText("Осадки"));
    fireEvent.click(screen.getByText("Агро-риск"));
    fireEvent.click(within(screen.getByTestId("agro-weather-tabs")).getByText("Рекомендации"));
    expect((await screen.findByTestId("agro-weather-recs")).textContent).toMatch(/СБОР УРОЖАЯ|Полив|ПОЛИВ/i);
    fireEvent.click(screen.getByTestId("agro-weather-macro-south"));
    fireEvent.click(screen.getByTestId("agro-weather-refresh"));
    const { agroOpsPost } = await import("../business-ops/opsApi");
    expect(vi.mocked(agroOpsPost).mock.calls.some((c) => String(c[0]).includes("/weather/refresh"))).toBe(true);
    fireEvent.change(screen.getByTestId("agro-weather-crop-select"), { target: { value: "Пшеница" } });
    fireEvent.click(within(screen.getByTestId("agro-weather-tabs")).getByText("30 дней"));
    expect((await screen.findByTestId("agro-weather-outlook-block")).textContent).toMatch(/климатической нормой|Недостаточно данных|повышенная/);
    fireEvent.click(screen.getByTestId("agro-weather-settings"));
  });

  it("keeps map geometry when weather request fails", async () => {
    const { agroOpsGet } = await import("../business-ops/opsApi");
    vi.mocked(agroOpsGet).mockImplementation(async (path: string) => {
      if (path.includes("/weather/")) {
        return { ok: false, status: 503, json: {} };
      }
      return { ok: true, status: 200, json: { items: [] } };
    });
    render(<AgroWeatherPanel headers={{}} />);
    expect(await screen.findByTestId("agro-weather-map")).toBeTruthy();
    expect(screen.getByTestId("agro-weather-oblast-odesa")).toBeTruthy();
    expect(await screen.findByTestId("agro-weather-error")).toBeTruthy();
  });
});
