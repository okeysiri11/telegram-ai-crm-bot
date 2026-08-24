/**
 * AGRO Live Data 1.3 — provider health, refresh, analysts, reviews, source drawer.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroIntelPanel } from "./AgroIntelPanel";

const providers = [
  {
    id: "usda_wasde",
    label_ru: "USDA / WASDE (минсельхоз США)",
    category: "world_balance",
    health_state: "REQUIRES_CONFIGURATION",
    connection_status: "NOT_CONFIGURED",
    status: "NOT_CONFIGURED",
    note_ru: "Требуется подключение источника",
    receives_ru: "Баланс пшеницы",
  },
  {
    id: "ua_customs_open_data",
    label_ru: "Таможня Украины / открытые данные",
    category: "trade",
    health_state: "CONNECTED",
    connection_status: "CONNECTED",
    last_success_at: "2026-08-16T12:00:00+00:00",
    note_ru: "Получено записей: 1",
    receives_ru: "Каталог открытых наборов",
    adapter_type: "open_data_api",
    url: "https://data.gov.ua/api/3/action/package_search",
  },
];

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
          item: providers[1],
          observations: [{ id: "obs-1", title: "Митна статистика", published_at: "2026-08-01T00:00:00" }],
        }),
      };
    }
    if (u.includes("/providers") && method === "GET") {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: providers }) };
    }
    if (u.includes("/reports/generate") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}")) as { kind?: string };
      if (body.kind === "fail") {
        return { ok: false, status: 500, json: async () => ({ ok: false, message_ru: "Источник недоступен" }) };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          item: {
            id: body.kind === "morning" ? "rev-morning-1" : "rev-evening-1",
            title: body.kind === "morning" ? "Утренний обзор" : "Вечерний обзор",
            sources_note_ru: "Цены, тонны и урожай не выдумываются.",
            sections: [
              {
                id: "trade",
                label_ru: "Экспорт / импорт",
                status: "DATA",
                bullets: [{ text: "Митна статистика", provider_id: "ua_customs_open_data", source_url: "https://data.gov.ua" }],
              },
            ],
          },
        }),
      };
    }
    if (u.includes("/reports")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    if (u.includes("/agents/run") && method === "POST") {
      return {
        ok: true,
        status: 201,
        json: async () => ({
          ok: true,
          item: { id: "agents-run-1", record_type: "agents_run", chief: { bias: "WATCH", confidence: 20, note_ru: "Цены и тонны не выдумываются." } },
        }),
      };
    }
    if (u.includes("/agents")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

describe("AGRO Live Data 1.3", () => {
  it("shows provider health screen", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const list = await screen.findByTestId("agro-intel-providers");
    expect(list.textContent).toMatch(/USDA/);
    expect(list.textContent).toMatch(/Требуется настройка|Источник не подключён/);
    expect(list.textContent).toMatch(/Таможня/);
    expect(list.textContent).toMatch(/Подключён/);
    expect(screen.getByText("Обновить все")).toBeTruthy();
  });

  it("refresh all shows loading then completion", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Обновить все"));
    expect(await screen.findByTestId("agro-intel-loading")).toBeTruthy();
    expect(await screen.findByText(/Опрос всех источников завершён/)).toBeTruthy();
  });

  it("run analysts stores output with id", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Запустить аналитиков"));
    const box = await screen.findByTestId("agro-intel-agents");
    expect(box.textContent).toMatch(/agents-run-1/);
    expect(screen.getByText(/Аналитики сохранены/)).toBeTruthy();
  });

  it("morning and evening reviews persist with id", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Утренний обзор"));
    expect(await screen.findByText(/rev-morning-1/)).toBeTruthy();
    fireEvent.click(screen.getByText("Вечерний обзор"));
    expect(await screen.findByText(/rev-evening-1/)).toBeTruthy();
    expect(screen.getByTestId("agro-intel-report").textContent).toMatch(/не выдумываются/);
  });

  it("opens source drawer from provider name", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fireEvent.click(screen.getByText("Таможня Украины / открытые данные"));
    const drawer = await screen.findByTestId("agro-intel-source-drawer");
    expect(drawer.textContent).toMatch(/CONNECTED/);
    expect(drawer.textContent).toMatch(/open_data_api/);
    expect(drawer.textContent).toMatch(/Митна статистика/);
  });

  it("shows error state when generate fails", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementationOnce(async (url: string) => {
      if (String(url).includes("/providers")) {
        return { ok: true, status: 200, json: async () => ({ ok: true, items: providers }) } as Response;
      }
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) } as Response;
    });
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    await screen.findByTestId("agro-intel-providers");
    fetchMock.mockImplementationOnce(async () => ({
      ok: false,
      status: 500,
      json: async () => ({ ok: false, message_ru: "Источник недоступен" }),
    }) as Response);
    fireEvent.click(screen.getByText("Утренний обзор"));
    expect(await screen.findByTestId("agro-intel-error")).toBeTruthy();
    expect(screen.getByText(/Источник недоступен/)).toBeTruthy();
  });
});
