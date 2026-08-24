/**
 * AGRO 2.5 — journey Back, deal task, weather back, notifications, demo labels.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { AgroDeal360 } from "./AgroDeal360";
import { AgroWeatherPanel } from "./AgroWeatherPanel";
import { AgroNotificationsPanel } from "./AgroNotificationsPanel";
import { agroOpsHref } from "./agroOpsNav";

const cc = {
  version: "AGRO_2_0",
  summary: [
    { id: "deals", label_ru: "Активные сделки", value: 1, view: "deals", empty: false },
    { id: "shipments", label_ru: "Поставки в пути", value: 0, hint_ru: "Нет активных перевозок", view: "logistics", filter: "IN_TRANSIT", empty: true },
  ],
  today: [],
  deals: { pipeline: [{ id: "new", label_ru: "Новая", count: 1, value: null }], items: [{ id: "d1", title: "Сделка 1", crop: "Пшеница" }] },
  shipments: { stages: [{ id: "in_transit", label_ru: "В пути", count: 0 }], items: [] },
  warehouses: { items: [], receipt_today: 0, issue_today: 0, top_crops: [] },
  markets: [],
  weather: { regions: [], has_data: false },
  intel: [],
  tasks: { today: [], overdue: [], week: [], meetings: [] },
  notifications: { unread: 0, by_category: [] },
  cash: { empty: true, empty_ru: "Остаток денежных средств не задан" },
  harvest: { empty: true, empty_ru: "Нет данных об урожае" },
  director_production: { cost_ha: null, cost_t: null, harvest_tonnes: null, crop_structure: [] },
};

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string, init?: RequestInit) => {
    const u = String(url);
    if (u.includes("/command-center") && !u.includes("/report")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, kpis: cc.summary, command_center: cc, cash: cc.cash, harvest: cc.harvest, onboarding: { steps: [] }, channels: {} }) };
    }
    if (u.includes("/dashboard")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, cards: {}, command_center: cc, onboarding: { steps: [] }, channels: {} }) };
    }
    if (u.includes("/crm/deal/")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          item: { id: "d1", number: "D-1", side: "buy", status: "negotiation", amount: 1000, currency: "UAH", remaining: 700, paid_pct: 30, allowed_statuses: ["approved"], crop: "Пшеница", quantity: 10 },
          calculation: { margin_pct: null, margin_ru: "не рассчитана" },
          items: [],
          checklist: [],
        }),
      };
    }
    if (u.includes("/entities/task") && init?.method === "POST") {
      return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "t1", title: "Проверить оплату" } }) };
    }
    if (u.includes("/weather/dashboard") || u.includes("/weather/overview")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          oblasts: [{ id: "ua-odesa", label_ru: "Одеська" }],
          region_cards: [{ id: "south", title_ru: "Юг" }],
          map: { regions: [{ id: "ua-odesa", label_ru: "Одеська" }] },
          last_updated: { display_ru: "сейчас" },
          confidence: { score: 40, label_ru: "средняя", text_ru: "Прогноз основан на данных 1 источника" },
          matrix: { columns: [{ id: "wheat", label_ru: "Пшеница", label_en: "Wheat" }], rows: [] },
        }),
      };
    }
    if (u.includes("/weather/forecast") || u.includes("/weather/agro-risk") || u.includes("/weather/recommendations") || u.includes("/weather/outlook")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          item: { temperature: 19 },
          forecast: [{ date: "2026-08-22", tmax: 22, precip: 0 }],
          agro_risk: { level: "Low", label_ru: "Низкий" },
          recommendations: [],
          monthly_outlook_ru: "Недостаточно данных для сравнения с климатической нормой.",
        }),
      };
    }
    if (u.includes("/crops/directory")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [{ name: "Пшеница" }] }) };
    }
    if (u.includes("/notifications/") && u.includes("/actions")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, linked: { record_kind: "deal", id: "d1" }, item: {} }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

function mount(path = "/workspace/agro") {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/agro" element={<AgroBusinessPage />} />
        <Route path="/workspace/agro/:sub" element={<AgroBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AGRO 2.5 journey and UX", () => {
  it("keeps deep links for command and counterparties", () => {
    expect(agroOpsHref("command")).toBe("/workspace/agro?view=command");
    expect(agroOpsHref("counterparties")).toBe("/workspace/agro?view=counterparties");
  });

  it("deal 360 can add task and has back control", async () => {
    const onQuick = vi.fn();
    render(
      <AgroDeal360 itemId="d1" headers={{}} canCreate canFinance canOperate onBack={() => undefined} onQuick={onQuick} onChanged={() => undefined} />,
    );
    expect(await screen.findByTestId("agro-deal-back")).toBeTruthy();
    fireEvent.click(screen.getByTestId("agro-deal-add-task"));
    expect(onQuick).toHaveBeenCalledWith("task");
    expect(await screen.findByTestId("agro-deal-task-save")).toBeTruthy();
    fireEvent.change(screen.getByPlaceholderText("Название задачи"), { target: { value: "Проверить оплату" } });
    fireEvent.click(screen.getByTestId("agro-deal-task-save"));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((c) => String(c[0]).includes("/entities/task"))).toBe(true));
  });

  it("weather region panel has back to map", async () => {
    render(<AgroWeatherPanel headers={{}} />);
    expect(await screen.findByTestId("agro-weather-panel")).toBeTruthy();
    const cards = await screen.findByTestId("agro-weather-region-cards");
    fireEvent.click(withinCardButton(cards));
    expect(await screen.findByTestId("agro-weather-back")).toBeTruthy();
    fireEvent.click(screen.getByTestId("agro-weather-back"));
    await waitFor(() => expect(screen.queryByTestId("agro-weather-back")).toBeNull());
  });

  it("notification linked title opens linked record action", async () => {
    const onOpen = vi.fn();
    render(
      <AgroNotificationsPanel
        headers={{}}
        canOperate
        notifications={[{ id: "n1", title: "[DEMO] сигнал сделки", status: "new", is_demo: true }]}
        onChanged={() => undefined}
        onOpenLinked={onOpen}
        onCreateRule={() => undefined}
        onCreateReminder={() => undefined}
      />,
    );
    fireEvent.click(screen.getByTestId("agro-notification-linked"));
    await waitFor(() => expect(onOpen).toHaveBeenCalled());
    expect(screen.getByTestId("agro-notification-linked").textContent).toMatch(/\[DEMO\]/);
  });

  it("command center uses Russian cost labels not Cost/ha", async () => {
    mount("/workspace/agro");
    expect(await screen.findByTestId("agro-command-center")).toBeTruthy();
    const root = screen.getByTestId("agro-command-center").textContent || "";
    expect(root).not.toMatch(/Cost\/ha/);
    expect(root).toMatch(/Себестоимость \/га|Нет активных перевозок|Остаток денежных средств не задан/);
  });
});

function withinCardButton(cards: HTMLElement) {
  const btn = cards.querySelector("button");
  if (!btn) throw new Error("no region card button");
  return btn;
}
