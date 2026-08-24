/**
 * Sprint AUTO 1.8.5 — remote/mobile access: status, drawer, tables, file accept.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/health")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        status: "ok",
        sprint: "AUTO_1.8.5",
        environment: "development",
        database: { online: true, engine: "postgres" },
        telegram: { status: "live", implemented: true, message_ru: "Новый бот не строится." },
      }),
    };
  }
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" } }) };
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
        finance: { purchase_cost: 0, expected_profit: 0, actual_profit: 0, expected_revenue: 0 },
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

describe("AUTO 1.8.5 remote / mobile access", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("keeps Auto workspace routes and mobile section drawer", async () => {
    mount("/workspace/auto?view=overview");
    expect(await screen.findByTestId("ops-mobile-nav-toggle")).toBeTruthy();
    fireEvent.click(screen.getByTestId("ops-mobile-nav-toggle"));
    const nav = screen.getByTestId("ops-side-nav").textContent || "";
    expect(nav).toMatch(/Обзор/);
    expect(nav).toMatch(/Автомобили/);
    expect(nav).toMatch(/Закупки/);
    expect(nav).toMatch(/Логистика/);
    expect(nav).toMatch(/Растаможка/);
    expect(nav).toMatch(/Клиенты/);
    expect(nav).toMatch(/Аналитика/);
    expect(nav).toMatch(/Настройки/);
  });

  it("settings show system status for AUTO 1.8.5", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-system-status")).toBeTruthy();
    expect(screen.getByTestId("auto-status-frontend").textContent).toMatch(/Frontend/i);
    expect(screen.getByTestId("auto-status-api").textContent).toMatch(/API/i);
    expect(screen.getByTestId("auto-status-database").textContent).toMatch(/Database/i);
    expect(screen.getByTestId("auto-status-telegram").textContent).toMatch(/Telegram/i);
    expect(screen.getByTestId("auto-status-environment").textContent).toMatch(/development|production/);
    expect(screen.getByTestId("auto-status-version").textContent).toMatch(/AUTO 1\.8\.5/);
  });

  it("document table uses a horizontal scroll wrapper", async () => {
    mount("/workspace/auto?view=documents");
    expect(await screen.findByTestId("auto-documents-table-wrap")).toBeTruthy();
    expect(screen.getByTestId("auto-documents-table")).toBeTruthy();
  });
});
