/**
 * AGRO 2.0 Operational Command Center — home UI, quick actions, search.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { AgroCommandCenter } from "./AgroCommandCenter";

const cc = {
  version: "AGRO_2_0",
  summary: [
    { id: "deals", label_ru: "Активные сделки", value: 0, hint_ru: "Нет данных", view: "deals", empty: true },
    { id: "shipments", label_ru: "Поставки в пути", value: 0, hint_ru: "Нет данных", view: "shipments", empty: true },
    { id: "stock", label_ru: "Склад, тонн", value: 0, unit: "т", hint_ru: "Нет данных", view: "warehouses", empty: true },
    { id: "payables", label_ru: "К оплате", value: 0, hint_ru: "Нет данных", view: "accounting", empty: true },
    { id: "overdue", label_ru: "Просрочено", value: 0, hint_ru: "Нет данных", view: "tasks", empty: true },
    { id: "critical", label_ru: "Критические события", value: 0, hint_ru: "Нет данных", view: "home", empty: true },
  ],
  today: [],
  deals: { pipeline: [{ id: "new", label_ru: "Новая", count: 0, value: null }], items: [] },
  shipments: { stages: [{ id: "in_transit", label_ru: "В пути", count: 0 }], items: [] },
  warehouses: { items: [], receipt_today: 0, issue_today: 0, top_crops: [] },
  markets: [],
  weather: { regions: [{ macro_id: "south", title_ru: "Юг", missing: true }], has_data: false },
  intel: [{ id: "ukraine", label_ru: "Украина", summary_ru: "Нет данных", missing: true }],
  tasks: { today: [], overdue: [], week: [], meetings: [] },
  notifications: { unread: 0, by_category: [] },
  sources_status: { ok: true, label_ru: "Нет данных о источниках", href: "/workspace/agro?view=settings&tab=sources" },
};

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string) => {
    const u = String(url);
    if (u.includes("/dashboard")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, cards: {}, command_center: cc, onboarding: { steps: [] }, channels: {} }) };
    }
    if (u.includes("/search")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, groups: [{ id: "counterparty", label_ru: "Контрагенты", items: [{ id: "1", kind: "counterparty", title: "ТОВ Зерно", view: "counterparties" }] }] }) };
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

describe("AGRO command center", () => {
  it("renders dashboard blocks and honest empty states", async () => {
    mount();
    expect(await screen.findByTestId("agro-command-center")).toBeTruthy();
    expect(screen.getByTestId("agro-cc-title").textContent).toMatch(/ОПЕРАЦИОННЫЙ ЦЕНТР/);
    expect(screen.getByTestId("agro-cc-summary")).toBeTruthy();
    expect(screen.getByTestId("agro-cc-today").textContent).toMatch(/Нет данных/);
    expect(screen.getByTestId("agro-cc-quick").textContent).toMatch(/Сделка/);
    expect(screen.getByTestId("agro-cc-deals").textContent).toMatch(/Новая/);
    expect(screen.getByTestId("agro-cc-weather").textContent).toMatch(/Нет данных/);
    expect(screen.getByTestId("agro-cc-intel").textContent).toMatch(/Украина/);
    expect(screen.getByTestId("agro-search-icon")).toBeTruthy();
  });

  it("opens universal quick create sheet", async () => {
    mount();
    await screen.findByTestId("agro-cc-quick");
    fireEvent.click(screen.getByText("+ Контрагент"));
    expect(await screen.findByTestId("agro-quick-sheet")).toBeTruthy();
    expect(screen.getByTestId("agro-quick-actions").textContent).toMatch(/Поставка/);
  });

  it("opens global search from top bar", async () => {
    mount();
    fireEvent.click(await screen.findByTestId("agro-search-icon"));
    expect(await screen.findByTestId("agro-global-search")).toBeTruthy();
  });

  it("standalone command center has clickable summary and pipeline", () => {
    const go: string[] = [];
    render(
      <AgroCommandCenter
        payload={cc}
        roleLabel="Директор"
        canCreate
        canFinance
        canOperate
        onGo={(v) => go.push(v)}
        onOpen={() => undefined}
        onQuick={() => undefined}
        onQuickKind={() => undefined}
        onSearch={() => undefined}
        onNotify={() => undefined}
        onTask={() => undefined}
        onAttach={() => undefined}
      />,
    );
    fireEvent.click(screen.getByTestId("agro-cc-summary-deals"));
    expect(go).toContain("deals");
    fireEvent.click(screen.getByText("Открыть карту"));
    expect(go).toContain("weather");
  });
});
