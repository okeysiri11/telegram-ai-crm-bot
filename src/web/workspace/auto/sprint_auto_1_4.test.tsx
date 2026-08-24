/**
 * Sprint AUTO 1.4 — live staff Telegram in the existing ADOS bot.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" } }) };
  }
  if (u.includes("/telegram/status")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        mode: "polling",
        last_successful_update: "2026-08-19T08:00:00+00:00",
        last_error: null,
        authorized_count: 2,
        notifications_sent_today: 3,
        authorized_users: [
          { telegram_id: 41001, role: "auto_director", label: "Директор" },
          { telegram_id: 41002, role: "auto_manager", label: "Менеджер" },
        ],
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
        intents: [{ command: "/vin <VIN>" }, { command: "/pay <VIN> <amount>" }],
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
  if (u.includes("/settings") || u.includes("/catalogs")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        roles: [{ id: "auto_director", label_ru: "Директор" }],
        catalogs: {
          vehicle_statuses: [{ id: "READY_FOR_SALE", label_ru: "Готов к продаже" }],
          expense_categories: [{ id: "STORAGE", label_ru: "Хранение" }],
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

describe("AUTO 1.4 live Telegram staff channel", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("telegram desk is live for staff and still does not claim a new bot", async () => {
    mount("/workspace/auto?view=telegram");
    const box = await screen.findByTestId("auto-telegram");
    expect(box.textContent).toMatch(/не строится/i);
    expect(box.textContent).toMatch(/live|сотрудник/i);
    expect(box.textContent).not.toMatch(/бот подключён и работает/i);
  });

  it("settings expose admin-only bot status fields", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    const status = await screen.findByTestId("auto-telegram-bot-status");
    expect(status.textContent).toMatch(/polling/i);
    expect(status.textContent).toMatch(/Последнее успешное обновление/);
    expect(status.textContent).toMatch(/Последняя ошибка/);
    expect(status.textContent).toMatch(/Авторизованных сотрудников/);
    expect(status.textContent).toMatch(/Уведомлений сегодня/);
    expect(screen.getAllByText(/Новый бот не строится/).length).toBeGreaterThan(0);
  });
});
