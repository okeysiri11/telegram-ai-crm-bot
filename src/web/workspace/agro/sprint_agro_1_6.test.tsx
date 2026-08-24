/**
 * AGRO 1.6 — source table columns, charts, MANUAL DATA.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";
import { AgroMarketsPanel } from "./AgroMarketsPanel";

const providers = [
  {
    id: "ec_agri",
    label_ru: "Еврокомиссия — рынок зерновых",
    category: "eu_market",
    group: "МЕЖДУНАРОДНЫЕ",
    health_state: "CONNECTED",
    connection_status: "CONNECTED",
    data_type_ru: "Числовой ряд",
    market_usable: true,
    last_success_at: "2026-08-17T12:00:00+00:00",
    observation_count: 12,
    freshness: "LIVE",
    error: "",
  },
];

vi.mock("../business-ops/opsApi", () => ({
  pick: (row: Record<string, unknown>, ...keys: string[]) => {
    for (const k of keys) {
      if (row && row[k] != null && String(row[k])) return String(row[k]);
    }
    return "";
  },
  agroOpsGet: vi.fn(async (path: string) => {
    if (path.includes("/providers") && !path.includes("/analytics")) {
      return { ok: true, status: 200, json: { ok: true, items: providers } };
    }
    if (path.includes("/analytics/dashboard")) {
      return {
        ok: true,
        status: 200,
        json: {
          freshness: [{ provider_id: "ec_agri", label_ru: "EU Crops", age_ru: "менее часа" }],
          gaps: ["Рыночные биржевые котировки не подключены (лицензия / ключ)."],
          series: {
            price: [
              { t: "2026-08-01", v: 288.37, unit: "EUR/t", source: "ec_agri" },
              { t: "2026-08-08", v: 270, unit: "EUR/t", source: "ec_agri" },
            ],
            production: [{ t: "2024", v: 40000000, unit: "t", source: "world_bank" }],
            yield_or_area: [{ t: "2024", v: 4200, unit: "kg/ha", source: "world_bank" }],
            trade: [{ t: "2024", v: 36, unit: "USD", source: "world_bank" }],
            fx: [{ t: "2026-08-17", v: 41.2, unit: "UAH", source: "fx_rates" }],
            weather: [{ t: "2026-08-17", v: 36, unit: "°C", source: "weather_provider" }],
          },
        },
      };
    }
    if (path === "/analytics" || path.endsWith("/analytics")) {
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }
    return { ok: true, status: 200, json: { ok: true, items: [] } };
  }),
  agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
}));

describe("AGRO 1.6 source table and charts", () => {
  it("provider table has 1.6 columns", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const list = await screen.findByTestId("agro-intel-providers");
    expect(list.textContent).toMatch(/Источник/);
    expect(list.textContent).toMatch(/Категория/);
    expect(list.textContent).toMatch(/Статус/);
    expect(list.textContent).toMatch(/Тип данных/);
    expect(list.textContent).toMatch(/Market usable/);
    expect(list.textContent).toMatch(/Наблюдений/);
    expect(list.textContent).toMatch(/Свежесть/);
    expect(list.textContent).toMatch(/Ошибки/);
    expect(list.textContent).toMatch(/Числовой ряд/);
  });

  it("analytics shows numeric charts", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    const charts = await screen.findByTestId("agro-analytics-charts");
    expect(charts.textContent).toMatch(/price/);
    expect(charts.textContent).toMatch(/288\.37|270/);
    expect(charts.textContent).toMatch(/fx/);
  });

  it("manual quotes are labelled MANUAL DATA", async () => {
    render(
      <AgroMarketsPanel
        headers={{}}
        canCreate
        canFinance
        markets={[{ id: "m1", name: "Локальный" }]}
        prices={[]}
        onChanged={() => undefined}
        onOpen={() => undefined}
        onAttach={() => undefined}
        onCreateCalc={() => undefined}
      />,
    );
    expect((await screen.findByTestId("agro-markets-panel")).textContent).toMatch(/MANUAL DATA/);
  });
});
