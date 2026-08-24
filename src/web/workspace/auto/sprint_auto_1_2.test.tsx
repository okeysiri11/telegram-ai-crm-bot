/**
 * Sprint AUTO 1.2 — customs operating desk.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "c1" } }) };
  }
  if (u.includes("/customs/cases") || u.includes("/customs?")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [],
        counts: { all: 0, pay: 0, problems: 0 },
        tabs: [{ id: "all", label_ru: "Все дела" }],
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { vehicles_total: 0, purchased: 0, in_transit: 0, at_port: 0, at_customs: 0, in_ukraine: 0, in_preparation: 0, for_sale: 0, sold: 0 },
        finance: { purchase_cost: 0, logistics: 0, customs: 0, other: 0, invested: 0, expected_revenue: 0, actual_revenue: 0, expected_profit: 0, actual_profit: 0, currency: "USD", from_records: true },
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
        implemented: false,
        status: "prepared",
        message_ru: "Команды Авто подготовлены. Новый бот не строится.",
        intents: [{ command: "/customs <VIN>" }],
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
        catalogs: {
          vehicle_statuses: [{ id: "CUSTOMS", label_ru: "Растаможка" }],
          expense_categories: [{ id: "IMPORT_VAT", label_ru: "НДС на импорт" }],
          customs_case_statuses: [{ id: "PAYMENT_PENDING", label_ru: "К оплате" }],
          currencies: ["USD", "EUR", "UAH", "GEL"],
        },
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

describe("AUTO 1.2 customs desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders customs operating tabs, not a filtered vehicle table", async () => {
    mount("/workspace/auto?view=customs");
    expect(await screen.findByTestId("auto-customs-desk")).toBeTruthy();
    const tabs = await screen.findByTestId("auto-customs-tabs");
    expect(tabs.textContent).toMatch(/Все дела/);
    expect(tabs.textContent).toMatch(/К оплате/);
    expect(tabs.textContent).toMatch(/Сертификация/);
    expect(tabs.textContent).toMatch(/Проблемные/);
    expect(screen.getByText(/Брокеры/)).toBeTruthy();
  });

  it("settings expose customs rates without claiming live customs API", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    expect(screen.getAllByText(/Растаможка/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Live-курс НБУ и калькулятор Гостаможни не подключены/)).toBeTruthy();
  });
});
