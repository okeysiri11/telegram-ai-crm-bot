/**
 * AGRO 2.1 CRM / Counterparty 360 / Deal 360 — desktop table vs mobile cards.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AgroCrmList } from "./AgroCrmList";
import { AgroCounterparty360 } from "./AgroCounterparty360";
import { AgroDeal360 } from "./AgroDeal360";
import { AgroQuickCreateSheet } from "./AgroQuickCreateSheet";

const headers = { "X-Role": "agro_director", "X-Organization-Id": "org" };

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.includes("/crm/list")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            items: [
              {
                id: "cp1",
                name: "АГРО ЮГ",
                types: ["supplier", "buyer"],
                region: "Одесская область",
                active_deals: 3,
                receivable: { UAH: 240000 },
                next_task: "сегодня",
                responsible: "Иван",
                risk: "LOW",
              },
            ],
            can_finance: true,
          },
        };
      }
      if (path.includes("/crm/analytics")) {
        return { ok: true, status: 200, json: { ok: true, active_counterparties: 1, new_30d: 1, active_deals: 3, aging: { overdue_count: 0 } } };
      }
      if (path.includes("/crm/counterparty/")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            item: { id: "cp1", name: "АГРО ЮГ", types: ["supplier"], status: "active", phone: "+38050111", email: "a@b.c", city: "Одесса", responsible: "Иван" },
            settlement: { receivable: { UAH: 240000 }, payable: {} },
            aging: { overdue_count: 0, oldest_days: null },
            crops: [{ crop: "Пшеница", direction_ru: "Продаёт", volume: 100 }],
            items: [],
            can_finance: true,
          },
        };
      }
      if (path.includes("/crm/deal/")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            item: { id: "d1", number: "d1", side: "sell", status: "draft", amount: 1000000, currency: "UAH", paid: 300000, remaining: 700000, paid_pct: 30, allowed_statuses: ["negotiation"], crop: "Пшеница", quantity: 100, price: 10000 },
            calculation: { cost_missing: true, margin_ru: "Себестоимость: нет данных. Маржа: не рассчитана" },
            checklist: [{ doc_type: "contract", status: "missing" }],
            items: [],
          },
        };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
  };
});

describe("AGRO 2.1 CRM", () => {
  it("desktop table and mobile cards use the same CRM payload", async () => {
    const { unmount } = render(
      <AgroCrmList headers={headers} canCreate canFinance canExport onOpen={() => undefined} onCreate={() => undefined} />,
    );
    expect(await screen.findByTestId("agro-crm-list")).toBeTruthy();
    expect(screen.getByTestId("agro-crm-table").textContent).toMatch(/АГРО ЮГ/);
    expect(screen.getByTestId("agro-crm-analytics").textContent).toMatch(/Активные контрагенты/);
    unmount();
    vi.stubGlobal("matchMedia", (q: string) => ({ matches: String(q).includes("767"), media: q, addEventListener: () => undefined, removeEventListener: () => undefined, addListener: () => undefined, removeListener: () => undefined, onchange: null, dispatchEvent: () => false }));
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 412 });
    render(<AgroCrmList headers={headers} canCreate canFinance canExport onOpen={() => undefined} onCreate={() => undefined} />);
    expect(await screen.findByTestId("agro-crm-cards")).toBeTruthy();
    expect(screen.getByTestId("agro-crm-cards").textContent).toMatch(/Активных сделок: 3/);
    expect(screen.getByTestId("agro-crm-cards").textContent).toMatch(/Открыть/);
  });

  it("counterparty 360 has compact mobile sections not 11 tiny tabs", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 412 });
    render(
      <MemoryRouter>
        <AgroCounterparty360 itemId="cp1" headers={headers} canCreate canFinance canOperate onBack={() => undefined} onOpenDeal={() => undefined} onQuick={() => undefined} onChanged={() => undefined} />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("agro-cp-360")).toBeTruthy();
    const tabs = screen.getByTestId("agro-cp-tabs").textContent || "";
    expect(tabs).toMatch(/Обзор/);
    expect(tabs).toMatch(/Ещё/);
    expect(tabs).not.toMatch(/КОММУНИКАЦИИ/);
    expect(screen.getByTestId("agro-cp-quick").textContent).toMatch(/Сделка/);
  });

  it("deal 360 shows honest margin empty state and remaining", async () => {
    render(
      <AgroDeal360 itemId="d1" headers={headers} canCreate canFinance canOperate onBack={() => undefined} onQuick={() => undefined} onChanged={() => undefined} />,
    );
    const root = await screen.findByTestId("agro-deal-360");
    expect(root.textContent).toMatch(/не рассчитана/);
    expect(root.textContent).toMatch(/700000/);
    expect(root.textContent).toMatch(/Переговоры/);
  });

  it("quick create still offers counterparty deal payment shipment document task", () => {
    render(
      <AgroQuickCreateSheet open kind={null} canCreate canFinance onSelect={() => undefined} onClose={() => undefined} />,
    );
    const txt = screen.getByTestId("agro-quick-actions").textContent || "";
    expect(txt).toMatch(/Контрагент/);
    expect(txt).toMatch(/Сделка/);
    expect(txt).toMatch(/Платёж/);
    expect(txt).toMatch(/Поставка/);
    expect(txt).toMatch(/Документ/);
    expect(txt).toMatch(/Задача/);
  });
});
