/**
 * Sprint AUTO 1.1 — logistics operating desk.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "s1" } }) };
  }
  if (u.includes("/logistics/shipments") || u.includes("/logistics?")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [],
        counts: { all: 0, sea: 0, problems: 0 },
        tabs: [{ id: "all", label_ru: "Все перевозки" }],
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
        intents: [{ command: "/logistics <VIN>" }],
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
          expense_categories: [{ id: "SEA_FREIGHT", label_ru: "Морской фрахт" }],
          shipment_types: [{ id: "CONTAINER", label_ru: "Контейнер" }],
          shipment_statuses: [{ id: "SEA_TRANSIT", label_ru: "В море" }],
          reference_ports: [{ unlocode: "USSAV", name: "Savannah" }],
          currencies: ["USD"],
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

describe("AUTO 1.1 logistics desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders logistics operating tabs, not a generic empty CRUD table", async () => {
    mount("/workspace/auto?view=logistics");
    expect(await screen.findByTestId("auto-logistics-desk")).toBeTruthy();
    const tabs = await screen.findByTestId("auto-logistics-tabs");
    expect(tabs.textContent).toMatch(/Все перевозки/);
    expect(tabs.textContent).toMatch(/Ожидают забора/);
    expect(tabs.textContent).toMatch(/В море/);
    expect(tabs.textContent).toMatch(/Проблемные/);
    expect(screen.getByText(/Где сейчас автомобиль/)).toBeTruthy();
    expect(screen.getByText(/Перевозчики/)).toBeTruthy();
    expect(screen.getByText(/Контейнеры/)).toBeTruthy();
  });

  it("settings expose logistics catalogs", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    expect(screen.getAllByText(/Логистика/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Live-tracking не включён/)).toBeTruthy();
  });
});
