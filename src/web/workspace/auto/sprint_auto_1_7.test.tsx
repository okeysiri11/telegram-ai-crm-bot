/**
 * Sprint AUTO 1.7 — logistics assignment, tracking buttons, providers, search.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/logistics/providers") && init?.method === "POST" && u.includes("/check")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: true, available: false, message_ru: "Автоматическое отслеживание недоступно" }),
    };
  }
  if (u.includes("/logistics/shipments/") && u.includes("/tracking")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        available: false,
        message_ru: "Автоматическое отслеживание недоступно",
        source_url: "https://line.example/track/1",
        last: { note_ru: "нет live AIS" },
        manual_event_allowed: true,
      }),
    };
  }
  if (u.includes("/logistics/shipments/s1")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        item: {
          id: "s1",
          vehicle_id: "veh-1",
          vehicle_title: "BMW X5",
          vin: "1HGCM82633A004352",
          status: "SEA_TRANSIT",
          status_ru: "В море",
          current_location: "Atlantic",
          tracking_url: "https://line.example/track/1",
          pipeline: [{ id: "vessel", label_ru: "Судно", state: "current" }],
          delay: { level: "green", delay_days: 0 },
          costs: { restricted: true },
          route: { label_ru: "Схема маршрута, не live-tracking", origin: "Savannah", destination: "Odesa" },
        },
        events: [{ id: "e1", created_at: "2026-08-19", description: "В море", source: "MANUAL", confirmation: "CONFIRMED" }],
      }),
    };
  }
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" } }) };
  }
  if (u.includes("/logistics/providers")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            id: "p1",
            name: "Demo Line",
            type: "ais",
            url: "https://line.example",
            api_key_env: "AUTO_TRACKING_KEY",
            status: "unavailable",
            status_ru: "Автоматическое отслеживание недоступно",
            last_check_at: "2026-08-19",
            last_error: "Переменная AUTO_TRACKING_KEY не задана",
            enabled: true,
          },
        ],
      }),
    };
  }
  if (u.includes("/search")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          { kind: "vehicle", id: "veh-1", title: "BMW X5", extra: "1HGCM82633A004352" },
          { kind: "shipment", id: "s1", title: "SHP-0001", extra: "BL-17" },
          { kind: "container", id: "c1", title: "MSCU1234567", extra: "" },
          { kind: "bol", id: "s1", title: "BL-17", extra: "SHP-0001" },
          { kind: "client", id: "cl1", title: "GlobeFly LLC", extra: "" },
        ],
      }),
    };
  }
  if (u.includes("/analytics/logistics")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        metrics: { avg_transit_days: 20, avg_delay_days: 3, avg_port_days: 2, avg_customs_days: 3, delayed_shipments: 0 },
      }),
    };
  }
  if (u.includes("/logistics/shipments") || u.includes("/logistics?")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            id: "s1",
            vehicle_title: "BMW X5",
            vin: "1HGCM82633A004352",
            status_ru: "В море",
            current_location: "Atlantic",
            delay: { level: "green", delay_days: 0 },
          },
        ],
        counts: { all: 1, sea: 1, problems: 0 },
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
        cards: { vehicles_total: 1, purchased: 0, in_transit: 1, at_port: 0, at_customs: 0, in_ukraine: 0, in_preparation: 0, for_sale: 0, sold: 0 },
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

describe("AUTO 1.7 logistics ops", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("tracking buttons call live endpoints and show fallback copy", async () => {
    mount("/workspace/auto?view=logistics");
    expect(await screen.findByTestId("auto-logistics-desk")).toBeTruthy();
    fireEvent.click(await screen.findByText("BMW X5"));
    const tracking = await screen.findByTestId("auto-tracking-actions");
    expect(tracking.textContent).toMatch(/Проверить/);
    expect(tracking.textContent).toMatch(/Последние данные/);
    expect(tracking.textContent).toMatch(/Открыть источник/);
    expect(tracking.textContent).toMatch(/Настройки/);
    fireEvent.click(screen.getByText("Проверить"));
    expect(await screen.findByText(/Автоматическое отслеживание недоступно/)).toBeTruthy();
    expect(screen.getByTestId("auto-event-source").textContent).toMatch(/MANUAL/);
  });

  it("settings list logistics providers without secrets", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-logistics-providers")).toBeTruthy();
    const box = screen.getByTestId("auto-logistics-providers");
    expect(box.textContent).toMatch(/Demo Line/);
    expect(box.textContent).toMatch(/AUTO_TRACKING_KEY/);
    expect(box.textContent).toMatch(/API key environment name/);
    expect(box.textContent).not.toMatch(/super-secret/);
  });

  it("director logistics analytics shows averages", async () => {
    mount("/workspace/auto?view=analytics");
    const desk = await screen.findByTestId("auto-analytics");
    const tabs = desk.querySelectorAll("button");
    const logisticsTab = Array.from(tabs).find((b) => b.textContent === "Логистика");
    expect(logisticsTab).toBeTruthy();
    fireEvent.click(logisticsTab!);
    const panel = await screen.findByTestId("auto-logistics-analytics");
    expect(panel.textContent).toMatch(/Среднее в пути/);
    expect(panel.textContent).toMatch(/Средняя задержка/);
    expect(panel.textContent).toMatch(/20/);
  });
});
