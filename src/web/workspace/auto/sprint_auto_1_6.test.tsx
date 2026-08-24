/**
 * Sprint AUTO 1.6 — documents desk, packages, no technical chrome.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AutoBusinessPage } from "./AutoBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x1" }, draft: true, message_ru: "Документ создан как черновик." }) };
  }
  if (u.includes("/documents/desk")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        kpis: { total: 11, missing: 2, review: 1, expiring: 0, rejected: 0 },
        items: [
          {
            id: "d1",
            title: "Коносамент",
            vehicle_title: "BMW X5",
            vin: "1HGCM82633A004352",
            client_name: "Іван",
            category: "logistics",
            document_type: "bill_of_lading",
            created_at: "2026-08-19",
            workflow_status: "DRAFT",
            uploaded_by: "manager",
          },
        ],
        generation_templates: [{ id: "sale_agreement_draft", name_ru: "Договор купли-продажи", draft: true }],
      }),
    };
  }
  if (u.includes("/documents/templates")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [{ id: "t1", name: "ownership document", stage: "registration", stage_name: "Регистрация", required: true, active: true }],
        stages: [{ id: "registration", name: "Регистрация", configurable: true }],
      }),
    };
  }
  if (u.includes("/analytics/director")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, summary_ru: "Документы требуют внимания: 2 авто" }) };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { vehicles_total: 1, purchased: 0, in_transit: 0, at_port: 0, at_customs: 0, in_ukraine: 0, in_preparation: 0, for_sale: 1, sold: 0 },
        finance: { purchase_cost: 0, logistics: 0, customs: 0, other: 0, invested: 0, expected_revenue: 0, actual_revenue: 0, expected_profit: 0, actual_profit: 0, currency: "USD", from_records: true },
        attention: [],
      }),
    };
  }
  if (u.includes("/vehicles")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [{ id: "veh-1", vin: "1HGCM82633A004352", manufacturer: "BMW", model: "X5", document_count: 12, documents_missing: 2, status: "READY_FOR_SALE" }],
      }),
    };
  }
  if (u.includes("/telegram")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: true, implemented: true, status: "live", message_ru: "Команды Авто включены в существующем боте ADOS. Новый бот не строится." }),
    };
  }
  if (u.includes("/settings") || u.includes("/catalogs")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        roles: [{ id: "auto_director", label_ru: "Директор" }],
        catalogs: { vehicle_statuses: [{ id: "READY_FOR_SALE", label_ru: "Готов к продаже" }], expense_categories: [], currencies: ["USD"] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path: string) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/auto" element={<AutoBusinessPage />} />
        <Route path="/workspace/auto/:sub" element={<AutoBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AUTO 1.6 documents desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("keeps compact 1.0 nav labels", async () => {
    mount("/workspace/auto?view=overview");
    const root = await screen.findByTestId("auto-business-cabinet");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Продажи/);
    expect(nav).toMatch(/Документы/);
    expect(nav).not.toMatch(/Пакет продажи/);
  });

  it("documents screen shows KPIs and register without storage keys", async () => {
    mount("/workspace/auto?view=documents");
    expect(await screen.findByTestId("auto-documents-desk")).toBeTruthy();
    expect(screen.getByText("Всего документов")).toBeTruthy();
    expect(screen.getByText("Не хватает")).toBeTruthy();
    expect(screen.getByTestId("auto-documents-table").textContent).toMatch(/Коносамент/);
    expect(screen.getByTestId("auto-documents-desk").textContent).not.toMatch(/checksum/i);
    expect(screen.getByTestId("auto-documents-desk").textContent).toMatch(/черновик/i);
  });

  it("settings expose configurable document templates", async () => {
    mount("/workspace/auto?view=settings");
    expect(await screen.findByTestId("auto-document-templates")).toBeTruthy();
    expect(screen.getByTestId("auto-document-templates").textContent).toMatch(/Регистрация/);
    expect(screen.getByTestId("auto-document-templates").textContent).toMatch(/не юридическая норма/i);
  });
});
