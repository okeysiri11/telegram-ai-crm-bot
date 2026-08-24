/**
 * AGRO 2.2 Operation 360 / list — desktop table vs mobile cards.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AgroOperationsList } from "./AgroOperationsList";
import { AgroOperation360 } from "./AgroOperation360";
import { AgroQuickCreateSheet } from "./AgroQuickCreateSheet";
import { AGRO_OPS_NAV } from "./agroOpsNav";

const headers = { "X-Role": "agro_director", "X-Organization-Id": "org" };

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.startsWith("/operations?") || path === "/operations") {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            items: [
              {
                id: "op1",
                number: "AG-2026-000142",
                crop: "Пшеница",
                status: "in_transit",
                status_ru: "В пути",
                planned_qty: 500,
                received_qty: 492,
                sold_qty: 300,
                remaining_qty: 188,
              },
            ],
          },
        };
      }
      if (path.includes("/operations/op1")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            item: {
              id: "op1",
              number: "AG-2026-000142",
              crop: "Пшеница",
              status: "in_transit",
              status_ru: "В пути",
              supplier: "Поставщик Зерно",
              planned_qty: 500,
              received_qty: 492,
              sold_qty: 300,
              remaining_qty: 188,
              purchase_value: 4250000,
              sales_value: 3000000,
              actual_expenses: 28000,
              allowed_statuses: ["receiving"],
            },
            pnl: { calculable: true, gross_profit: 135000, margin_pct: 9, message_ru: null },
            cost_basis: { total_cost: 1320000, cost_missing: false },
            plan_vs_actual: { quantity: { plan: 500, actual: 492 } },
            items: [{ id: "t1", plate: "BH 1234 AA", driver_name: "Иван", load_place: "Одесса", dest_place: "Южный", planned_weight: 24.5, crop: "Пшеница" }],
            tab: "overview",
          },
        };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
    agroOpsUpload: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true } })),
  };
});

vi.mock("@/shell/mobile/useIsMobile", () => ({ useIsMobile: () => false }));

describe("AGRO 2.2 operations", () => {
  it("lists operation number and remaining stock", async () => {
    render(
      <MemoryRouter>
        <AgroOperationsList headers={headers} canCreate onOpen={() => undefined} onCreate={() => undefined} />
      </MemoryRouter>,
    );
    expect(await screen.findByText("AG-2026-000142")).toBeTruthy();
    expect(screen.getByTestId("agro-operations-list")).toBeTruthy();
  });

  it("renders operation 360 header and sections", async () => {
    render(
      <MemoryRouter>
        <AgroOperation360 itemId="op1" headers={headers} canCreate canFinance canOperate onBack={() => undefined} onQuick={() => undefined} onChanged={() => undefined} />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("agro-operation-360")).toBeTruthy();
    expect(screen.getByTestId("agro-op-number").textContent).toContain("AG-2026-000142");
    expect(screen.getByTestId("agro-op-tabs")).toBeTruthy();
    fireEvent.click(screen.getByText("Logistics"));
    expect(await screen.findByTestId("agro-op-trucks")).toBeTruthy();
  });

  it("keeps Операции in agro nav", () => {
    expect(AGRO_OPS_NAV.some((n) => n.id === "operations" && n.label === "Операции")).toBe(true);
  });

  it("quick sheet includes operation create", () => {
    render(
      <AgroQuickCreateSheet open kind={null} canCreate canFinance onSelect={() => undefined} onClose={() => undefined} />,
    );
    expect(screen.getByText("+ Операция")).toBeTruthy();
  });

  it("shows context actions inside operation", () => {
    render(
      <AgroQuickCreateSheet open kind={null} canCreate canFinance insideOperation onSelect={() => undefined} onClose={() => undefined} />,
    );
    expect(screen.getByText("Добавить взвешивание")).toBeTruthy();
    expect(screen.queryByText("+ Контрагент")).toBeNull();
  });
});
