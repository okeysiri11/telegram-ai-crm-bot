/**
 * AGRO Operations 1.1 — logistics / markets / warehouses / provider health.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { AgroIntelPanel } from "./AgroIntelPanel";

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string, init?: RequestInit) => {
    const u = String(url);
    if (u.includes("/providers/") && u.includes("/probe") && init?.method === "POST") {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, item: { id: "usda_wasde", note_ru: "Получено записей: 1", connection_status: "CONNECTED" } }),
      };
    }
    if (u.includes("/providers") && !u.includes("/probe")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [
            {
              id: "usda_wasde",
              label_ru: "USDA / WASDE (минсельхоз США)",
              category: "world_balance",
              status: "NOT_CONFIGURED",
              connection_status: "NOT_CONFIGURED",
              note_ru: "Источник не подключён",
              receives_ru: "Баланс пшеницы",
            },
            { id: "manual_import", label_ru: "Ручной импорт / RSS", status: "LIVE", connection_status: "CONNECTED", note_ru: "Доступен" },
          ],
        }),
      };
    }
    if (u.includes("/logistics/dashboard")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, cards: { active_trips: 0, free_vehicles: 0 } }) };
    }
    if (u.includes("/markets/dashboard") || u.includes("/markets/history") || u.includes("/warehouses/dashboard")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, current: [], points: [], cards: { capacity_total: 0, occupied: 0 }, by_crop: [] }) };
    }
    if (u.includes("/dashboard")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          cards: {},
          onboarding: { steps: ["Создать контрагента"] },
          channels: { in_app: { id: "in_app", connected: true, label_ru: "В приложении" } },
        }),
      };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

function mount(path: string) {
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

describe("AGRO Operations 1.1", () => {
  it("logistics empty state is operational", async () => {
    mount("/workspace/agro?view=logistics");
    expect(await screen.findByTestId("agro-logistics-panel")).toBeTruthy();
    expect(screen.getAllByText(/Транспорт ещё не добавлен/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Добавить перевозчика/).length).toBeGreaterThan(0);
  });

  it("markets empty state offers add market/price", async () => {
    mount("/workspace/agro?view=markets");
    expect(await screen.findByTestId("agro-markets-panel")).toBeTruthy();
    expect(screen.getAllByText(/Рынки ещё не настроены/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Подключить источник/).length).toBeGreaterThan(0);
  });

  it("warehouses empty state offers add warehouse", async () => {
    mount("/workspace/agro?view=warehouses");
    expect(await screen.findByTestId("agro-warehouse-panel")).toBeTruthy();
    expect(screen.getAllByText(/Склады ещё не добавлены/).length).toBeGreaterThan(0);
  });

  it("intel health table can probe a source", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const list = await screen.findByTestId("agro-intel-providers");
    expect(list.textContent).toMatch(/USDA/);
    expect(list.textContent).toMatch(/Источник не подключён|Требуется/);
    fireEvent.click(screen.getAllByText("Проверить")[0]);
    expect(await screen.findByText(/Получено записей|Проверка завершена/)).toBeTruthy();
  });
});
