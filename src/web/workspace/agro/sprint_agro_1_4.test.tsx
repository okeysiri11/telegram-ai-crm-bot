/**
 * AGRO 1.4 — source table, history, analysts, reviews, no dead buttons.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroIntelPanel } from "./AgroIntelPanel";

const providers = [
  {
    id: "ua_customs_open_data",
    label_ru: "Таможня Украины / открытые данные",
    category: "trade",
    group: "УКРАИНА (официальные)",
    health_state: "CONNECTED",
    connection_status: "CONNECTED",
    last_success_at: "2026-08-17T06:42:00+00:00",
    observation_count: 8,
    next_check_at: "2026-08-17T18:42:00+00:00",
    receives_ru: "Экспорт / импорт",
    adapter_type: "open_data_api",
    url: "https://data.gov.ua/api/3/action/package_search",
    license_note_ru: "data.gov.ua",
    cadence: "daily",
  },
];

const report = {
  id: "rev-morning-14",
  title: "Утренний обзор (по запросу)",
  report_date: "2026-08-17",
  generated_at: "2026-08-17T06:12:00+00:00",
  confidence: 42,
  sources_count: 2,
  sources_note_ru: "Цены, тонны и урожай не выдумываются.",
  data_gaps_json: ["EU Crops временно недоступен."],
  sections: [
    {
      id: "trade",
      label_ru: "Экспорт / импорт",
      status: "DATA",
      bullets: [{ text: "Митна статистика", provider_id: "ua_customs_open_data", source_url: "https://data.gov.ua" }],
    },
  ],
};

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string, init?: RequestInit) => {
    const u = String(url);
    const method = init?.method || "GET";
    if (u.includes("/providers/refresh-all") && method === "POST") {
      await new Promise((r) => setTimeout(r, 30));
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    if (u.includes("/providers/ua_customs_open_data") && method === "GET") {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          item: providers[0],
          observations: [{ id: "obs-1", title: "Митна статистика", published_at: "2026-08-01T00:00:00" }],
        }),
      };
    }
    if (u.includes("/providers") && method === "GET") {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: providers }) };
    }
    if (u.includes("/reports/generate") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}")) as { kind?: string; open_latest?: boolean; generate?: boolean };
      if (body.open_latest && !body.generate) {
        return { ok: true, status: 200, json: async () => ({ ok: true, item: null, offer_generate: true, message_ru: "Обзора за сегодня нет. Сформировать сейчас?" }) };
      }
      return { ok: true, status: 200, json: async () => ({ ok: true, item: report }) };
    }
    if (u.includes("/reports")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [report] }) };
    }
    if (u.includes("/agents/run") && method === "POST") {
      return {
        ok: true,
        status: 201,
        json: async () => ({
          ok: true,
          item: {
            id: "agents-run-14",
            record_type: "agents_run",
            specialists_executed: ["ukraine", "trade", "chief"],
            chief: { bias: "WATCH", confidence: 42, note_ru: "Цены и тонны не выдумываются." },
          },
        }),
      };
    }
    if (u.includes("/agents")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

describe("AGRO 1.4", () => {
  it("source health table has records column and actions", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const list = await screen.findByTestId("agro-intel-providers");
    expect(list.textContent).toMatch(/Таможня/);
    expect(list.textContent).toMatch(/Наблюдений/);
    expect(screen.getByText("Проверить")).toBeTruthy();
    expect(screen.getByText("Последние данные")).toBeTruthy();
    expect(screen.getByText("Открыть источник")).toBeTruthy();
    expect(screen.getByText("Настройки")).toBeTruthy();
  });

  it("latest data drawer shows normalized records", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Последние данные"));
    const drawer = await screen.findByTestId("agro-intel-source-drawer");
    expect(drawer.textContent).toMatch(/Митна статистика/);
    expect(drawer.textContent).toMatch(/наблюдения/);
  });

  it("run analysts stores a new run id", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Запустить аналитиков"));
    expect(await screen.findByText(/agents-run-14/)).toBeTruthy();
  });

  it("morning review offers generate then opens stored report", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Утренний обзор"));
    expect(await screen.findByRole("button", { name: "Сформировать сейчас" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Сформировать сейчас" }));
    expect(await screen.findByText(/rev-morning-14/)).toBeTruthy();
  });

  it("history opens stored report", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const hist = await screen.findByTestId("agro-intel-history");
    expect(hist.textContent).toMatch(/Утренний обзор/);
    fireEvent.click(screen.getAllByText("Открыть")[0]);
    expect(screen.getByTestId("agro-intel-report").textContent).toMatch(/rev-morning-14/);
  });
});
