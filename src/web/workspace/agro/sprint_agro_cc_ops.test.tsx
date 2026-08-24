/**
 * AGRO Command Center ops: URL views, landing skip, aggregated fetch.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { WorkspaceLandingGate } from "@/modules/WorkspaceLandingGate";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { agroOpsHref } from "./agroOpsNav";

const cc = {
  version: "AGRO_2_0",
  summary: [
    { id: "shipments", label_ru: "Поставки в пути", value: 0, hint_ru: "Нет активных перевозок", view: "logistics", filter: "IN_TRANSIT", empty: true },
    { id: "overdue", label_ru: "Просрочено", value: 0, hint_ru: "Нет просроченных оплат", view: "accounting", filter: "overdue", empty: true },
  ],
  today: [],
  deals: { pipeline: [], items: [] },
  shipments: { stages: [{ id: "in_transit", label_ru: "В пути", count: 0 }], items: [] },
  warehouses: { items: [], receipt_today: 0, issue_today: 0, top_crops: [] },
  markets: [],
  weather: { regions: [], has_data: false },
  intel: [],
  tasks: { today: [], overdue: [], week: [], meetings: [] },
  notifications: { unread: 0, by_category: [] },
  cash: { empty: true, empty_ru: "Остаток денежных средств не задан" },
  harvest: { empty: true, empty_ru: "Нет данных об урожае" },
};

const seen: string[] = [];

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string) => {
    const u = String(url);
    seen.push(u);
    if (u.includes("/command-center") && !u.includes("/report")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, kpis: cc.summary, command_center: cc, cash: cc.cash, harvest: cc.harvest, onboarding: { steps: [] }, channels: {} }) };
    }
    if (u.includes("/dashboard")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, cards: {}, command_center: cc, onboarding: { steps: [] }, channels: {} }) };
    }
    if (u.includes("/command-center/report")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, text: "АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА", html: "<h1>АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА</h1>" }) };
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

describe("AGRO command center ops URLs", () => {
  it("command href is a deep route", () => {
    expect(agroOpsHref("command")).toBe("/workspace/agro?view=command");
    expect(agroOpsHref("home")).toBe("/workspace/agro");
  });

  it("desktop /workspace/agro opens ops cabinet instead of catalog landing", () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1280 });
    render(
      <MemoryRouter initialEntries={["/workspace/agro"]}>
        <WorkspaceLandingGate landingId="agro">
          <p data-testid="agro-ops-cabinet">cabinet</p>
        </WorkspaceLandingGate>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("agro-ops-cabinet")).toBeTruthy();
    expect(screen.queryByText("Открыть ферму")).toBeNull();
  });

  it("home and command views render command center", async () => {
    mount("/workspace/agro");
    expect(await screen.findByTestId("agro-command-center")).toBeTruthy();
    mount("/workspace/agro?view=command");
    expect(await screen.findByTestId("agro-command-route")).toBeTruthy();
  });

  it("home does not fetch dozens of entity lists", async () => {
    seen.length = 0;
    mount("/workspace/agro");
    await screen.findByTestId("agro-command-center");
    const entityGets = seen.filter((u) => u.includes("/entities/"));
    expect(entityGets.length).toBeLessThan(4);
    expect(seen.some((u) => u.includes("/command-center"))).toBe(true);
  });

  it("honest empty states for cash harvest logistics", async () => {
    mount("/workspace/agro");
    expect(await screen.findByTestId("agro-cc-cash")).toBeTruthy();
    expect(screen.getByTestId("agro-cc-cash").textContent).toMatch(/Остаток денежных средств не задан/);
    expect(screen.getByTestId("agro-cc-harvest").textContent).toMatch(/Нет данных об урожае/);
    expect(screen.getByTestId("agro-cc-shipments").textContent).toMatch(/Нет активных перевозок/);
  });
});
