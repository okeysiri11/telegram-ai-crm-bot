/**
 * Sprint AUTO 1.5 — director analytics / finance desks.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" } }) };
  }
  if (u.includes("/analytics/director")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        summary_ru: "24 автомобиля в системе. $346000 капитала вложено. 4 автомобиля требуют внимания.",
        risks: [{ vehicle_id: "veh-1", message_ru: "2 low-margin vehicles" }],
      }),
    };
  }
  if (u.includes("/analytics/economics")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            vehicle_id: "veh-1",
            title: "BMW X5",
            vin: "1HGCM82633A004352",
            purchase_date: "2026-06-01",
            status_ru: "Продан",
            days_in_cycle: 40,
            purchase: 18000,
            logistics: 1100,
            customs: 4000,
            repair: 800,
            cost: 23900,
            sale_price: 28000,
            profit: 4100,
            margin_pct: 14.6,
            manager: "mgr-a",
            sold: true,
            quality: "PARTIAL",
            completeness_note_ru: "Себестоимость неполная: не внесена стоимость таможенного брокера.",
          },
        ],
      }),
    };
  }
  if (u.includes("/analytics/finance")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { received: 5000, spent: 2000, receivables: 25000, upcoming_expenses: 1500, frozen_capital: 211000, realized_profit: 4100, forecast_profit: 8000 },
        labels_ru: {
          received: "Деньги получены",
          spent: "Деньги потрачены",
          receivables: "Дебиторка клиентов",
          frozen_capital: "Замороженный капитал",
        },
      }),
    };
  }
  if (u.includes("/analytics/cashflow")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        opening_known: true,
        opening_balance: 80000,
        gap: { date: "2026-09-15", incoming: 42000, outgoing: 67000, gap: -25000, message_ru: "⚠ Возможный кассовый разрыв" },
        items: [{ date: "2026-09-15", incoming: 42000, outgoing: 67000, net: -25000, running_balance: -25000 }],
      }),
    };
  }
  if (u.includes("/analytics/risks")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [{ vehicle_id: "veh-1", message_ru: "Маржа 8% ниже 10%" }] }) };
  }
  if (u.includes("/analytics/managers")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [{ manager_id: "mgr-a", active_clients: 3, vehicles_assigned: 4, overdue_tasks: 1, profit: 4100, avg_margin: 14.6 }],
        employee_scoring: false,
        note_ru: "Сбалансированные счётчики. Рейтинга по выручке нет.",
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { vehicles_total: 24, purchased: 4, in_transit: 8, at_port: 1, at_customs: 4, in_ukraine: 0, in_preparation: 2, for_sale: 7, sold: 3 },
        finance: { purchase_cost: 0, logistics: 0, customs: 0, other: 0, invested: 346000, expected_revenue: 0, actual_revenue: 0, expected_profit: 0, actual_profit: 0, currency: "USD", from_records: true },
        attention: [],
      }),
    };
  }
  if (u.includes("/telegram")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        implemented: true,
        status: "live",
        message_ru: "Команды Авто включены в существующем боте ADOS. Новый бот не строится.",
      }),
    };
  }
  if (u.includes("/settings") || u.includes("/catalogs")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        roles: [{ id: "auto_director", label_ru: "Директор" }],
        catalogs: { vehicle_statuses: [{ id: "SOLD", label_ru: "Продан" }], expense_categories: [{ id: "PURCHASE", label_ru: "Цена автомобиля" }], currencies: ["USD"] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path: string) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/auto" element={<AutoBusinessPage />} />
        <Route path="/workspace/auto/:sub" element={<AutoBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AUTO 1.5 director analytics", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("overview shows На сегодня from real director summary", async () => {
    mount("/workspace/auto?view=overview");
    expect(await screen.findByTestId("auto-director-summary")).toBeTruthy();
    expect(screen.getByTestId("auto-director-summary").textContent).toMatch(/24 автомобиля/);
    expect(screen.getByText("Автомобилей всего")).toBeTruthy();
  });

  it("economics table has filters and drill-down", async () => {
    mount("/workspace/auto?view=analytics");
    expect(await screen.findByTestId("auto-analytics")).toBeTruthy();
    expect(screen.getByTestId("auto-economics-filters").textContent).toMatch(/Прибыльные/);
    expect(screen.getByTestId("auto-economics-table").textContent).toMatch(/BMW X5/);
    expect(screen.getByTestId("auto-economics-table").textContent).toMatch(/Себестоимость неполная/);
    fireEvent.click(screen.getByText("Низкая маржа"));
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("filter=low_margin"))).toBe(true);
    fireEvent.click(screen.getByText("BMW X5"));
  });

  it("finance cash-flow shows gap warning", async () => {
    mount("/workspace/auto?view=finance");
    expect(await screen.findByTestId("auto-finance")).toBeTruthy();
    fireEvent.click(screen.getByText("Cash Flow"));
    expect(await screen.findByTestId("auto-cash-gap")).toBeTruthy();
    expect(screen.getByTestId("auto-cash-gap").textContent).toMatch(/кассовый разрыв/i);
  });

  it("risks and managers stay business-language without ranking-by-revenue", async () => {
    mount("/workspace/auto?view=analytics");
    await screen.findByTestId("auto-analytics");
    fireEvent.click(screen.getByText("Риски"));
    expect(await screen.findByTestId("auto-risks")).toBeTruthy();
    expect(screen.getByTestId("auto-risks").textContent).toMatch(/Маржа/);
    fireEvent.click(screen.getByText("Менеджеры"));
    expect(await screen.findByTestId("auto-managers-analytics")).toBeTruthy();
    expect(screen.getByTestId("auto-managers-analytics").textContent).toMatch(/Рейтинга по выручке нет/);
  });
});
