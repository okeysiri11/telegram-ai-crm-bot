/**
 * Sprint AUTO 1.3 — CRM / reports operating desk.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "d1" } }) };
  }
  if (u.includes("/crm/deals")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [],
        counts: { all: 0, leads: 0, active: 0, reserved: 0, paying: 0, done: 0, problems: 0 },
        tabs: [{ id: "all", label_ru: "Все сделки" }],
      }),
    };
  }
  if (u.includes("/reports")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [],
        types: [
          { id: "sales", label_ru: "Продажи" },
          { id: "vehicle_profit", label_ru: "Прибыль по автомобилям" },
          { id: "expenses", label_ru: "Расходы" },
          { id: "receipts", label_ru: "Поступления" },
          { id: "client_debt", label_ru: "Задолженность клиентов" },
          { id: "managers", label_ru: "Работа менеджеров" },
          { id: "funnel", label_ru: "Воронка продаж" },
          { id: "in_stock", label_ru: "Автомобили в наличии" },
          { id: "in_transit", label_ru: "Автомобили в пути" },
        ],
        employee_scoring: false,
        note_ru: "Отчёт по фактическим записям.",
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
        intents: [{ command: "/client <name>" }, { command: "/deal <VIN>" }],
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
          vehicle_statuses: [{ id: "RESERVED", label_ru: "Зарезервирован" }],
          expense_categories: [{ id: "PURCHASE", label_ru: "Цена автомобиля" }],
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

describe("AUTO 1.3 CRM desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders CRM operating tabs instead of a client table", async () => {
    mount("/workspace/auto?view=clients");
    expect(await screen.findByTestId("auto-crm-desk")).toBeTruthy();
    const tabs = await screen.findByTestId("auto-crm-tabs");
    expect(tabs.textContent).toMatch(/Лиды/);
    expect(tabs.textContent).toMatch(/Резерв/);
    expect(tabs.textContent).toMatch(/Оплата/);
    expect(tabs.textContent).toMatch(/Закрытые/);
    expect(screen.getByText(/кто клиент, какая машина, какой этап/i)).toBeTruthy();
  });

  it("reports list business types without employee scoring chrome", async () => {
    mount("/workspace/auto?view=reports");
    expect(await screen.findByTestId("auto-reports")).toBeTruthy();
    const types = await screen.findByTestId("auto-report-types");
    expect(types.textContent).toMatch(/Продажи/);
    expect(types.textContent).toMatch(/Воронка продаж/);
    expect(types.textContent).toMatch(/Работа менеджеров/);
    expect(types.textContent).toMatch(/Автомобили в наличии/);
    expect(types.textContent).toMatch(/Автомобили в пути/);
  });

  it("settings expose CRM policy and demo without claiming live scoring", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    expect(screen.getByText(/Паспорт и адрес на бэкенде закрыты/)).toBeTruthy();
    expect(screen.getByText(/Балльной оценки менеджеров нет/)).toBeTruthy();
    expect(screen.getByText(/Создать демо-сделку/)).toBeTruthy();
  });
});
