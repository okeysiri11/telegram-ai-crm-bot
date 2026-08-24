/**
 * Sprint 49.1 — operational cabinets: forms, watchlist isolation, chart provider honesty.
 */

import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { BeautyBusinessPage } from "../beauty/BeautyBusinessPage";
import { CafeBusinessPage } from "../cafe/CafeBusinessPage";
import { CryptoOtcDeskPage } from "../crypto/CryptoOtcDeskPage";
import {
  NullChartProvider,
  CryptoTaChartProvider,
  setMarketChartProvider,
} from "../crypto/chartProvider";
import { loadWatchlist, saveWatchlist, loadAnalyses, saveAnalyses } from "../crypto/otcPrefs";

const store: Record<string, unknown> = {
  customers: [],
  services: [],
  appointments: [],
  employees: [],
  branches: [],
  orders: [],
  menu: [],
  tables: [],
  staff: [],
  reservations: [],
  shifts: [],
};

function jsonRes(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  };
}

vi.stubGlobal(
  "fetch",
  vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method || "GET").toUpperCase();
    if (url.includes("/bootstrap") && method === "POST") {
      store.customers = [{ customer_id: "c1", name: "Anna" }];
      store.services = [{ service_id: "s1", name: "Manicure", price: 40, duration_min: 60 }];
      store.employees = [{ employee_id: "e1", name: "Ivy", role: "master" }];
      store.branches = [{ branch_id: "b1", name: "Main" }];
      store.appointments = [];
      store.menu = [{ item_id: "m1", name: "Latte", price: 5, category: "coffee" }];
      store.tables = [{ table_id: "t1", name: "T1", seats: 4, zone: "main" }];
      store.staff = [{ staff_id: "st1", name: "Bob", role: "waiter" }];
      store.customers = [{ customer_id: "c1", name: "Anna" }];
      store.orders = [];
      store.shifts = [];
      return jsonRes({ ok: true }, 201);
    }
    if (url.includes("/appointments") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      if (body.appointment_id && body.status) {
        store.appointments = (store.appointments as Record<string, unknown>[]).map((a) =>
          a.appointment_id === body.appointment_id ? { ...a, status: body.status } : a,
        );
        return jsonRes({ appointment_id: body.appointment_id, status: body.status });
      }
      const appt = {
        appointment_id: `ap_${(store.appointments as unknown[]).length + 1}`,
        ...body,
        status: "booked",
      };
      (store.appointments as unknown[]).push(appt);
      return jsonRes(appt, 201);
    }
    if (url.includes("/orders") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const order = {
        order_id: `ord_${(store.orders as unknown[]).length + 1}`,
        ...body,
        total: 5,
        status: "Новый",
      };
      (store.orders as unknown[]).push(order);
      return jsonRes(order, 201);
    }
    if (url.includes("/shifts") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      if (body.action === "close") {
        store.shifts = (store.shifts as Record<string, unknown>[]).map((s) =>
          s.shift_id === body.shift_id ? { ...s, status: "Закрыта" } : s,
        );
        return jsonRes({ shift_id: body.shift_id, status: "Закрыта" });
      }
      const sh = { shift_id: "sh1", staff_id: body.staff_id, status: "Открыта", role: "waiter", date: "2026-08-10", start: "now", end: "" };
      (store.shifts as unknown[]).push(sh);
      return jsonRes(sh, 201);
    }
    if (url.includes("/customers")) return jsonRes({ items: store.customers });
    if (url.includes("/services")) return jsonRes({ items: store.services });
    if (url.includes("/appointments")) return jsonRes({ items: store.appointments });
    if (url.includes("/employees")) return jsonRes({ items: store.employees });
    if (url.includes("/branches")) return jsonRes({ items: store.branches });
    if (url.includes("/orders")) return jsonRes({ items: store.orders });
    if (url.includes("/menu")) return jsonRes({ items: store.menu });
    if (url.includes("/tables")) return jsonRes({ items: store.tables });
    if (url.includes("/staff")) return jsonRes({ items: store.staff });
    if (url.includes("/reservations")) return jsonRes({ items: store.reservations || [] });
    if (url.includes("/shifts")) return jsonRes({ items: store.shifts });
    if (url.includes("/dashboard")) return jsonRes({});
    if (url.includes("/markets")) return jsonRes({ items: [] });
    if (url.includes("/portfolio")) return jsonRes({});
    if (url.includes("/tradingview") || url.includes("/charts")) {
      return jsonRes({ status: "disconnected" }, 200);
    }
    return jsonRes({}, 404);
  }),
);

function mount(path: string, el: React.ReactElement) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/beauty" element={el} />
        <Route path="/workspace/cafe" element={el} />
        <Route path="/workspace/crypto" element={el} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 49.1 ops cabinets", () => {
  beforeEach(() => {
    localStorage.clear();
    store.appointments = [];
    store.orders = [];
    store.shifts = [];
  });

  it("Beauty can create appointment after bootstrap and persists in list", async () => {
    mount("/workspace/beauty", <BeautyBusinessPage />);
    const root = await screen.findByTestId("beauty-business-cabinet");
    fireEvent.click(screen.getByRole("button", { name: "Загрузить демо-данные" }));
    await waitFor(() => expect((store.customers as unknown[]).length).toBeGreaterThan(0));
    const nav = root.querySelector('[aria-label="Разделы"]')!;
    fireEvent.click(Array.from(nav.querySelectorAll("button")).find((b) => b.textContent === "Записи")!);
    fireEvent.click(screen.getAllByRole("button", { name: "+ Новая запись" })[0]);
    await screen.findByTestId("beauty-appointment-form");
    const selects = screen.getByTestId("beauty-appointment-form").querySelectorAll("select");
    fireEvent.change(selects[0], { target: { value: "c1" } });
    fireEvent.change(selects[1], { target: { value: "s1" } });
    fireEvent.change(selects[2], { target: { value: "e1" } });
    const start = screen
      .getByTestId("beauty-appointment-form")
      .querySelector('input[type="datetime-local"]') as HTMLInputElement;
    fireEvent.change(start, { target: { value: "2026-08-11T10:00" } });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить запись" }));
    await waitFor(() => expect((store.appointments as unknown[]).length).toBe(1));
  });

  it("Cafe order form persists event type", async () => {
    mount("/workspace/cafe", <CafeBusinessPage />);
    const root = await screen.findByTestId("cafe-business-cabinet");
    fireEvent.click(screen.getByRole("button", { name: "Загрузить демо-данные" }));
    await waitFor(() => expect((store.menu as unknown[]).length).toBeGreaterThan(0));
    const nav = root.querySelector('[aria-label="Разделы"]')!;
    fireEvent.click(Array.from(nav.querySelectorAll("button")).find((b) => b.textContent === "Заказы")!);
    fireEvent.click(screen.getAllByRole("button", { name: "+ Новый заказ" })[0]);
    await screen.findByTestId("cafe-order-form");
    const selects = screen.getByTestId("cafe-order-form").querySelectorAll("select");
    fireEvent.change(selects[0], { target: { value: "Банкет" } });
    fireEvent.change(selects[1], { target: { value: "c1" } });
    fireEvent.change(selects[2], { target: { value: "t1" } });
    fireEvent.change(selects[3], { target: { value: "m1" } });
    fireEvent.click(screen.getByRole("button", { name: "Создать заказ" }));
    await waitFor(() => {
      expect((store.orders as Record<string, unknown>[])[0]?.order_type).toBe("Банкет");
    });
  });

  it("Crypto watchlist is tenant-scoped and chart provider does not fabricate quotes", async () => {
    saveWatchlist(["BTC/USDT"], "tenant-a");
    saveWatchlist(["ETH/USDT"], "tenant-b");
    expect(loadWatchlist("tenant-a")).toEqual(["BTC/USDT"]);
    expect(loadWatchlist("tenant-b")).toEqual(["ETH/USDT"]);

    const nullP = new NullChartProvider();
    const snap = await nullP.loadChart("BTC/USDT", "1h");
    expect(snap.quote).toBeNull();
    expect(snap.status).toBe("not_connected");
    expect(snap.message.toLowerCase()).toContain("недоступен");

    const ta = new CryptoTaChartProvider(async () => ({ ok: true, status: 200, json: { status: "offline" } }));
    setMarketChartProvider(ta);
    const snap2 = await ta.loadChart("BTC/USDT", "5m");
    expect(snap2.quote).toBeNull();
    expect(["needs_config", "not_connected", "error"]).toContain(snap2.status);

    mount("/workspace/crypto", <CryptoOtcDeskPage />);
    const root = await screen.findByTestId("crypto-otc-desk");
    expect(root).toBeTruthy();
    expect(screen.queryByText("Enterprise Reuse")).toBeNull();
    const nav = root.querySelector('[aria-label="Разделы"]')!;
    fireEvent.click(Array.from(nav.querySelectorAll("button")).find((b) => b.textContent === "Графики")!);
    expect(await screen.findByTestId("otc-chart-workspace")).toBeTruthy();
    fireEvent.click(Array.from(nav.querySelectorAll("button")).find((b) => b.textContent === "Анализы")!);
    expect(await screen.findByTestId("otc-analyses")).toBeTruthy();
    const configs = loadAnalyses();
    saveAnalyses([{ ...configs[0], enabled: true }]);
    expect(loadAnalyses()[0].enabled).toBe(true);
  });
});
