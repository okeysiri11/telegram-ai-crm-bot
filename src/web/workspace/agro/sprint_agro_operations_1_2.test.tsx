/**
 * AGRO Operations 1.2 — notifications, calendar, crops, deliveries, demo.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AgroBusinessPage } from "./AgroBusinessPage";
import { AgroCalendarPanel } from "./AgroCalendarPanel";
import { AgroNotificationsPanel } from "./AgroNotificationsPanel";

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string, init?: RequestInit) => {
    const u = String(url);
    if (u.includes("/crops/directory")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, items: [{ name: "Пшеница", available: 0, demand: 0, gap: 0, in_catalog: true }] }),
      };
    }
    if (u.includes("/notifications/") && u.includes("/actions") && init?.method === "POST") {
      return { ok: true, status: 200, json: async () => ({ ok: true, item: { id: "n1", status: "read" }, linked: { id: "p1", record_kind: "market_price" } }) };
    }
    if (u.includes("/bootstrap") && init?.method === "POST") {
      return { ok: true, status: 201, json: async () => ({ ok: true, item: {} }) };
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

describe("AGRO Operations 1.2", () => {
  it("notifications empty state and actions", async () => {
    mount("/workspace/agro?view=notifications");
    expect(await screen.findByTestId("agro-notifications-panel")).toBeTruthy();
    expect(screen.getAllByText(/Пока нет сигналов/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Создать правило/).length).toBeGreaterThan(0);
    render(
      <AgroNotificationsPanel
        headers={{}}
        canOperate
        notifications={[{ id: "n1", title: "[DEMO] сигнал", status: "new", is_demo: true }]}
        onChanged={() => undefined}
        onOpenLinked={() => undefined}
        onCreateRule={() => undefined}
        onCreateReminder={() => undefined}
      />,
    );
    expect(screen.getByText(/Открыть/)).toBeTruthy();
    expect(screen.getByText(/Отметить прочитанным/)).toBeTruthy();
    expect(screen.getByText(/Создать задачу/)).toBeTruthy();
    fireEvent.click(screen.getAllByText("Отметить прочитанным")[0]);
    expect(await screen.findByText(/Сделано: mark_read/)).toBeTruthy();
  });

  it("calendar month view renders empty month", async () => {
    render(<AgroCalendarPanel headers={{}} canOperate events={[]} onChanged={() => undefined} onOpen={() => undefined} />);
    expect(screen.getByTestId("agro-calendar-month")).toBeTruthy();
    expect(screen.getByText("Пн")).toBeTruthy();
    expect(screen.getByText(/Создать событие/)).toBeTruthy();
  });

  it("crop directory shows wheat at zero balance", async () => {
    mount("/workspace/agro?view=crops");
    const table = await screen.findByTestId("agro-crop-directory");
    expect(table.textContent).toMatch(/Пшеница/);
    expect(table.textContent).toMatch(/0/);
  });

  it("deliveries empty state", async () => {
    mount("/workspace/agro?view=shipments");
    expect(await screen.findByTestId("agro-deliveries-panel")).toBeTruthy();
    expect(screen.getAllByText(/Поставок ещё нет/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Добавить поставку/).length).toBeGreaterThan(0);
  });

  it("demo load button is explicit", async () => {
    mount("/workspace/agro");
    expect(await screen.findByText("Загрузить демо AGRO")).toBeTruthy();
  });
});
