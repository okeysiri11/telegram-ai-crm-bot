/**
 * AGRO 2.6 — nav modules and operational panels.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AGRO_OPS_NAV, AGRO_DOMAIN_MENU_LABELS } from "./agroOpsNav";
import { AgroSowingsPage, AgroWorksPage, AgroHarvestPage, AgroMachinery26Page, AgroCropsCatalog26 } from "./AgroOps26Modules";

const headers = { "X-Organization-Id": "org-demo", "X-Role": "agro_director", "X-Workspace-Id": "agro" };

vi.mock("../business-ops/opsApi", () => {
  return {
    pick: (row: Record<string, unknown>, key: string) => String(row?.[key] ?? ""),
    agroOpsGet: vi.fn(async (path: string) => {
      if (path.startsWith("/sowings")) {
        return { ok: true, json: { items: [{ id: "s1", title: "Посев пшеницы", field_name: "Поле 1", crop: "Пшеница", status_ru: "План", area_ha: 10, total_operation_cost: 5000, cost_per_hectare: 500 }] } };
      }
      if (path.startsWith("/works")) {
        return { ok: true, json: { items: [{ id: "w1", title: "Подготовка почвы", field_name: "Поле 1", operation_ru: "Подготовка почвы", status_ru: "Запланировано", status: "planned" }], work_types: [] } };
      }
      if (path.startsWith("/harvests")) {
        return { ok: true, json: { items: [{ id: "h1", title: "Урожай", field_name: "Поле 1", crop: "Пшеница", actual_tonnes: 60, yield_t_ha: 6, linked_warehouse: false }] } };
      }
      if (path.startsWith("/machines")) {
        return { ok: true, json: { items: [{ id: "m1", name: "Трактор 1", type_ru: "Трактор", status_ru: "Свободна", plate: "AA1111" }], types: [], statuses: [] } };
      }
      if (path.startsWith("/agro-crops")) {
        return { ok: true, json: { items: [{ id: "c1", name: "Пшеница", variety: "Одесская", season: "озимая", producer: "—" }] } };
      }
      if (path.startsWith("/fields")) {
        return { ok: true, json: { items: [{ id: "f1", name: "Поле 1" }] } };
      }
      if (path.startsWith("/entities/warehouse")) {
        return { ok: true, json: { items: [] } };
      }
      return { ok: true, json: { items: [] } };
    }),
    agroOpsPost: vi.fn(async () => ({ ok: true, json: { ok: true, message_ru: "Сохранено" } })),
  };
});

describe("AGRO 2.6 navigation", () => {
  it("exposes operational production modules in Russian", () => {
    for (const id of ["fields", "crops", "sowing", "machinery", "works", "harvest"]) {
      expect(AGRO_OPS_NAV.some((n) => n.id === id)).toBe(true);
    }
    expect(AGRO_OPS_NAV.find((n) => n.id === "fields")?.label).toBe("Поля");
    expect(AGRO_OPS_NAV.find((n) => n.id === "machinery")?.label).toBe("Техника");
    for (const label of AGRO_DOMAIN_MENU_LABELS) {
      expect(AGRO_OPS_NAV.some((n) => n.label === label)).toBe(false);
    }
  });
});

describe("AGRO 2.6 modules", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sowing list with create action", async () => {
    render(<AgroSowingsPage headers={headers} canCreate onOpenField={() => undefined} />);
    expect(await screen.findByTestId("agro-sowings-page")).toBeTruthy();
    expect(screen.getByTestId("agro-sowing-create")).toBeTruthy();
    expect(await screen.findByText("Посев пшеницы")).toBeTruthy();
  });

  it("renders works and harvest modules", async () => {
    const { unmount } = render(<AgroWorksPage headers={headers} canCreate onOpenField={() => undefined} />);
    expect(await screen.findByTestId("agro-works-page")).toBeTruthy();
    expect(await screen.findByText("Подготовка почвы")).toBeTruthy();
    unmount();
    render(<AgroHarvestPage headers={headers} canCreate onOpenField={() => undefined} />);
    expect(await screen.findByTestId("agro-harvest-page")).toBeTruthy();
    expect(await screen.findByText(/60/)).toBeTruthy();
  });

  it("renders machinery and crop catalog", async () => {
    const { unmount } = render(
      <AgroMachinery26Page headers={headers} canCreate onOpen={() => undefined} onBack={() => undefined} />,
    );
    expect(await screen.findByTestId("agro-machinery-26")).toBeTruthy();
    expect(await screen.findByText("Трактор 1")).toBeTruthy();
    unmount();
    render(<AgroCropsCatalog26 headers={headers} canCreate />);
    expect(await screen.findByTestId("agro-crops-26")).toBeTruthy();
    expect(await screen.findByText("Пшеница")).toBeTruthy();
  });
});
