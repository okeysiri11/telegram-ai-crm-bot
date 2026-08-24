/**
 * AGRO 2.3 Field 360 / land bank / machinery.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroProductionPage, AgroMachineryPage } from "./AgroProductionPage";
import { AGRO_OPS_NAV, AGRO_DOMAIN_MENU_LABELS } from "./agroOpsNav";

const headers = { "X-Role": "agro_director", "X-Organization-Id": "org" };

vi.mock("../business-ops/opsApi", async () => {
  const actual = await vi.importActual<typeof import("../business-ops/opsApi")>("../business-ops/opsApi");
  return {
    ...actual,
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.startsWith("/fields/map")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            layer: "crop",
            features: [{ id: "f1", name: "Поле 17", area_ha: 124, crop: "Пшеница", color: "#c9a227", polygon: [[10, 10], [80, 10], [80, 60], [10, 60]] }],
            legend: [{ id: "Пшеница", label_ru: "Пшеница", color: "#c9a227" }],
          },
        };
      }
      if (path.startsWith("/fields/f1")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            item: { id: "f1", name: "Поле 17", area_ha: 124, crop: "Пшеница", status_ru: "Вегетация", yield_t_ha: null, cost_ha: null, weather: { label_ru: "нет данных" } },
            plan_vs_actual: { yield: { plan: null, actual: null, difference: null } },
            items: [{ id: "w1", title: "Опрыскивание", status: "planned" }],
            tab: "works",
            trace_forward: [],
          },
        };
      }
      if (path === "/fields" || path.startsWith("/fields?")) {
        return {
          ok: true,
          status: 200,
          json: {
            ok: true,
            land_bank_ha: 124,
            items: [{ id: "f1", name: "Поле 17", area_ha: 124, crop: "Пшеница", status_ru: "Вегетация", today_work: "Опрыскивание 08:00", weather_risk: "Rain tomorrow" }],
          },
        };
      }
      if (path.startsWith("/entities/machine")) {
        return { ok: true, status: 200, json: { ok: true, items: [{ id: "m1", plate: "TR-1", engine_hours: 12 }] } };
      }
      return { ok: true, status: 200, json: { ok: true, items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, status: 201, json: { ok: true, item: { id: "x" } } })),
  };
});

describe("AGRO 2.3 production UI", () => {
  it("keeps fields and machines in operational nav without domain catalog leftovers", () => {
    expect(AGRO_OPS_NAV.some((n) => n.id === "fields" && n.label === "Поля")).toBe(true);
    expect(AGRO_OPS_NAV.some((n) => n.id === "machinery" && n.label === "Техника")).toBe(true);
    expect(AGRO_OPS_NAV.some((n) => n.id === "sowing")).toBe(true);
    expect(AGRO_OPS_NAV.some((n) => n.id === "works")).toBe(true);
    expect(AGRO_OPS_NAV.some((n) => n.id === "harvest")).toBe(true);
    for (const label of AGRO_DOMAIN_MENU_LABELS) {
      expect(AGRO_OPS_NAV.some((n) => n.label === label)).toBe(false);
    }
  });

  it("renders compact field cards and map legend", async () => {
    render(
      <AgroProductionPage
        headers={headers}
        canCreate
        canFinance
        onOpen={() => undefined}
        onBack={() => undefined}
        onGo={() => undefined}
      />,
    );
    expect(await screen.findByText("Поле 17")).toBeTruthy();
    expect(screen.getAllByText(/124 ha/).length).toBeGreaterThan(0);
    expect(screen.getByTestId("agro-field-map")).toBeTruthy();
    expect(screen.getByTestId("agro-map-legend")).toBeTruthy();
    expect(screen.getByText("Загрузить демо AGRO Production")).toBeTruthy();
  });

  it("opens Field 360 with work start and no invented yield", async () => {
    render(
      <AgroProductionPage
        headers={headers}
        canCreate
        canFinance
        fieldId="f1"
        tab="works"
        onOpen={() => undefined}
        onBack={() => undefined}
        onGo={() => undefined}
      />,
    );
    expect(await screen.findByTestId("agro-field-360")).toBeTruthy();
    expect(screen.getAllByText("нет данных").length).toBeGreaterThan(0);
    expect(screen.getByTestId("agro-work-start")).toBeTruthy();
    fireEvent.click(screen.getByTestId("agro-field-quick"));
    expect(screen.getByText("Создать работу")).toBeTruthy();
    expect(screen.getByText("Добавить материал")).toBeTruthy();
    expect(screen.getByText("Добавить фото")).toBeTruthy();
    expect(screen.getByTestId("agro-field-back")).toBeTruthy();
  });

  it("renders machinery page", async () => {
    render(<AgroMachineryPage headers={headers} canCreate />);
    expect(await screen.findByTestId("agro-machinery-page")).toBeTruthy();
    expect(screen.getByText(/TR-1/)).toBeTruthy();
  });
});
