/**
 * Sprint AUTO 1.8 — customs summary, analytics averages, correction, export.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/analytics/customs")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        from_records: true,
        metrics: {
          avg_customs_duration: 12,
          avg_duty: 1000,
          avg_excise: 2000,
          avg_vat: 3000,
          avg_customs_total: 6000,
          avg_certification_cost: 400,
          avg_registration_cost: 250,
          avg_landed_cost: 22000,
          vehicles_delayed: 1,
          blocked_vehicles: 0,
        },
      }),
    };
  }
  if (u.includes("/customs/cases/c1")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        item: {
          id: "c1",
          vehicle_id: "veh-1",
          vehicle_title: "BMW X5",
          vin: "1HGCM82633A004352",
          status: "DOCUMENTS_PREP",
          status_ru: "Сбор документов",
          broker_name: "Odesa Broker",
          declaration_number: "MD-18",
          answers: { where: "Одесса", happening: "Сбор документов", next_stage: "Подано брокеру / таможне", todo: [] },
          checklist: { items: [], missing: [] },
          calculation: { restricted: false, ok: false, disclaimer_ru: "Расчёт по ставкам организации. Не официальный калькулятор Гостаможни." },
          payments: { restricted: false, paid: 0, due: 0, lines: [] },
          pipeline: [{ id: "docs", label_ru: "Документы", state: "current" }],
          certification: { status_ru: "Не начата" },
          registration: { status_ru: "Пакет не готов" },
          timeline: [],
        },
        summary: {
          title_ru: "Сводка по растаможке",
          vehicle: "BMW X5",
          vin: "1HGCM82633A004352",
          broker: "Odesa Broker",
          declaration: "MD-18",
        },
      }),
    };
  }
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" } }) };
  }
  if (u.includes("/customs/cases") || u.includes("/customs?")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            id: "c1",
            vehicle_title: "BMW X5",
            vin: "1HGCM82633A004352",
            status: "DOCUMENTS_PREP",
            status_ru: "Сбор документов",
            answers: { where: "Одесса" },
          },
        ],
        counts: { all: 1, pay: 0, problems: 0 },
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
        cards: { vehicles_total: 1, purchased: 0, in_transit: 0, at_port: 0, at_customs: 1, in_ukraine: 0, in_preparation: 0, for_sale: 0, sold: 0 },
        finance: { purchase_cost: 0, logistics: 0, customs: 0, other: 0, invested: 0, expected_revenue: 0, actual_revenue: 0, expected_profit: 0, actual_profit: 0, currency: "USD", from_records: true },
        attention: [],
      }),
    };
  }
  if (u.includes("/telegram/status")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, implemented: true, status: "live", message_ru: "Новый бот не строится." }) };
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
        catalogs: {
          vehicle_statuses: [{ id: "CUSTOMS", label_ru: "Таможня" }],
          expense_categories: [{ id: "DUTY", label_ru: "Мито" }],
          customs_case_statuses: [{ id: "DOCUMENTS_PREP", label_ru: "Сбор документов" }],
          currencies: ["USD"],
        },
      }),
    };
  }
  if (u.includes("/analytics/director")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, summary_ru: "1 автомобиль в системе." }) };
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

describe("AUTO 1.8 customs ops", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("shows printable customs summary and correction controls", async () => {
    mount("/workspace/auto?view=customs");
    expect(await screen.findByTestId("auto-customs-desk")).toBeTruthy();
    expect(screen.getByTestId("auto-customs-export").textContent).toMatch(/CSV customs_cases/);
    fireEvent.click(await screen.findByText("BMW X5"));
    expect(await screen.findByTestId("auto-customs-summary")).toBeTruthy();
    const summary = screen.getByTestId("auto-customs-summary");
    expect(summary.textContent).toMatch(/Сводка по растаможке|BMW X5|1HGCM82633A004352|Odesa Broker|MD-18/);
    expect(screen.getByTestId("auto-customs-correction").textContent).toMatch(/Коррекция статуса/);
    expect(screen.getByPlaceholderText("Причина коррекции")).toBeTruthy();
  });

  it("director customs analytics shows real-record averages", async () => {
    mount("/workspace/auto?view=analytics");
    const desk = await screen.findByTestId("auto-analytics");
    const tabs = desk.querySelectorAll("button");
    const customsTab = Array.from(tabs).find((b) => b.textContent === "Таможня");
    expect(customsTab).toBeTruthy();
    fireEvent.click(customsTab!);
    const panel = await screen.findByTestId("auto-customs-analytics");
    expect(panel.textContent).toMatch(/Средняя длительность/);
    expect(panel.textContent).toMatch(/12/);
    expect(panel.textContent).toMatch(/Среднее мито/);
    expect(panel.textContent).toMatch(/Задержанные/);
  });

  it("settings still do not claim live Гостаможня", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-settings")).toBeTruthy();
    expect(screen.getByText(/Live-курс НБУ и калькулятор Гостаможни не подключены/)).toBeTruthy();
  });
});
