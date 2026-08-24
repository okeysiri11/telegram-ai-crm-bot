/**
 * AGRO Production 1.0 — home, settings honesty, intel panel.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { AgroIntelPanel } from "./AgroIntelPanel";

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string) => {
    const u = String(url);
    if (u.includes("/dashboard")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          cards: { counterparties: 0, farmers: 0, companies: 0, suppliers: 0, buyers: 0, active_contracts: 0, receivables: 0, payables: 0, active_shipments: 0, tasks_today: 0, overdue_tasks: 0 },
          onboarding: { steps: ["Создать контрагента", "Создать сделку"] },
          channels: { in_app: { id: "in_app", connected: true, label_ru: "В приложении" }, telegram: { id: "telegram", connected: false, label_ru: "Telegram — не настроен" } },
        }),
      };
    }
    if (u.includes("/providers")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [
            { id: "usda_wasde", label_ru: "USDA / WASDE", group: "МЕЖДУНАРОДНЫЕ", status: "NOT_CONFIGURED", note_ru: "Требуется подключение источника" },
            { id: "manual_import", label_ru: "Ручной импорт / RSS", group: "РУЧНОЙ ВВОД", status: "LIVE", note_ru: "Доступен" },
          ],
        }),
      };
    }
    if (u.includes("/finance/summary")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, receivables_total: 0, payables_total: 0, overdue_total: 0 }) };
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

describe("AGRO Production 1.0", () => {
  it("home shows operational command center", async () => {
    mount("/workspace/agro");
    expect(await screen.findByTestId("agro-home")).toBeTruthy();
    expect(await screen.findByTestId("agro-command-center")).toBeTruthy();
    expect(screen.getByTestId("agro-cc-title").textContent).toMatch(/ОПЕРАЦИОННЫЙ ЦЕНТР/);
    expect(screen.getByTestId("agro-cc-quick").textContent).toMatch(/Контрагент/);
  });

  it("settings show honest source status", async () => {
    mount("/workspace/agro?view=settings");
    expect(await screen.findByTestId("agro-settings-sources")).toBeTruthy();
    expect(screen.getByText(/Источник не подключён|Требуется подключение/)).toBeTruthy();
    expect(screen.getByText(/Telegram — не настроен/)).toBeTruthy();
  });

  it("intel panel never claims USDA is live", async () => {
    render(<AgroIntelPanel headers={{}} canOperate canIntel />);
    const list = await screen.findByTestId("agro-intel-providers");
    expect(list.textContent).toMatch(/USDA/);
    expect(list.textContent).toMatch(/Источник не подключён|Требуется/);
    expect(list.textContent).not.toMatch(/USDA \/ WASDE · МЕЖДУНАРОДНЫЕАктуально/);
  });
});
