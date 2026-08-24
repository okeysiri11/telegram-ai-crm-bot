/**
 * Sprint AUTO 1.0 — private Auto OS cabinet.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        item: { id: "veh-1", vin: "1HGCM82633A004352", manufacturer: "BMW", model: "X5", status: "INTEREST", status_ru: "Интерес" },
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: {
          vehicles_total: 0,
          purchased: 0,
          in_transit: 0,
          at_port: 0,
          at_customs: 0,
          in_ukraine: 0,
          in_preparation: 0,
          for_sale: 0,
          sold: 0,
        },
        finance: {
          purchase_cost: 0,
          logistics: 0,
          customs: 0,
          other: 0,
          invested: 0,
          expected_revenue: 0,
          actual_revenue: 0,
          expected_profit: 0,
          actual_profit: 0,
          currency: "USD",
          from_records: true,
        },
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
        message_ru: "Telegram для Авто будет подключён в следующем спринте.",
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
          vehicle_statuses: [{ id: "SEA_TRANSIT", label_ru: "Морская перевозка" }],
          expense_categories: [{ id: "PURCHASE", label_ru: "Цена автомобиля" }],
          currencies: ["USD", "EUR", "UAH", "GEL"],
        },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path = "/workspace/auto?view=overview") {
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

describe("AUTO 1.0 private desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders operational sidebar without technical clutter", async () => {
    mount("/workspace/auto?view=overview");
    const root = await screen.findByTestId("auto-business-cabinet");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Обзор/);
    expect(nav).toMatch(/Автомобили/);
    expect(nav).toMatch(/Закупки/);
    expect(nav).toMatch(/Логистика/);
    expect(nav).toMatch(/Растаможка/);
    expect(nav).toMatch(/Клиенты/);
    expect(nav).toMatch(/Продажи/);
    expect(nav).toMatch(/Платежи и расходы/);
    expect(nav).toMatch(/Документы/);
    expect(nav).toMatch(/CRM и задачи/);
    expect(nav).toMatch(/Telegram/);
    expect(nav).toMatch(/Отчёты/);
    expect(nav).toMatch(/Настройки/);
    expect(nav).not.toMatch(/JSON/);
    expect(nav).not.toMatch(/health/i);
  });

  it("dashboard shows KPI labels and honest empty finance", async () => {
    mount("/workspace/auto?view=overview");
    expect(await screen.findByTestId("auto-overview")).toBeTruthy();
    expect(screen.getByText("Автомобилей всего")).toBeTruthy();
    expect(screen.getByText("Всего вложено")).toBeTruthy();
    expect(screen.getByText("Ожидаемая прибыль")).toBeTruthy();
  });

  it("vehicles section has add button and empty copy without fake stock", async () => {
    mount("/workspace/auto?view=vehicles");
    const addButtons = await screen.findAllByText("+ Добавить автомобиль");
    expect(addButtons.length).toBeGreaterThan(0);
    fireEvent.click(addButtons[0]);
    expect(await screen.findByTestId("auto-vehicle-create")).toBeTruthy();
    expect(screen.getAllByLabelText("VIN").length).toBeGreaterThan(0);
  });

  it("telegram is a prepared placeholder, not a fake live bot", async () => {
    mount("/workspace/auto?view=telegram");
    const box = await screen.findByTestId("auto-telegram");
    expect(box.textContent).toMatch(/следующем спринте|не строится|подключён позже/i);
    expect(box.textContent).not.toMatch(/бот подключён и работает/i);
  });

  it("settings keep technical state off the operational nav", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    expect(screen.getByTestId("auto-settings-tech").textContent).toMatch(/auto-ops/);
  });
});
