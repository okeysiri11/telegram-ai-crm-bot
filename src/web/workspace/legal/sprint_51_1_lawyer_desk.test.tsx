/**
 * Sprint 51.1 — Lawyer CRUD / calendar / archive / integrations UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LawyerBusinessPage } from "./LawyerBusinessPage";

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
          cards: { clients: 1, open_cases: 1, hearings_today: 0, open_deadlines: 0, pending_approvals: 0 },
          google_calendar: { status: "needs_config" },
        }),
      };
    }
    if (u.includes("/integrations/calendars")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [
            { provider: "google", label_ru: "Google Calendar", status: "needs_config", message_ru: "Требуется настройка Google OAuth" },
            { provider: "microsoft", label_ru: "Microsoft Calendar", status: "coming_soon", message_ru: "Скоро / Требуется настройка" },
          ],
        }),
      };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

function mount(path = "/workspace/legal") {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/legal" element={<LawyerBusinessPage />} />
        <Route path="/workspace/legal/:sub" element={<LawyerBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 51.1 Lawyer desk", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("shows inbox, archive and calendar nav", async () => {
    mount();
    const root = await screen.findByTestId("lawyer-business-cabinet");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Входящие/);
    expect(nav).toMatch(/Архив/);
    expect(nav).toMatch(/Календарь/);
  });

  it("renders month calendar view", async () => {
    mount("/workspace/legal?view=calendar");
    expect(await screen.findByTestId("lawyer-calendar-month")).toBeTruthy();
    expect(screen.getByTestId("lawyer-calendar-toolbar").textContent).toMatch(/Месяц/);
    expect(screen.getByTestId("lawyer-calendar-filters").textContent).toMatch(/Заседания/);
  });

  it("shows Google OAuth honest state in settings", async () => {
    mount("/workspace/legal?view=settings");
    const card = await screen.findByTestId("lawyer-calendar-integrations");
    expect(card.textContent).toMatch(/Google Calendar/);
    expect(card.textContent).toMatch(/Требуется настройка Google OAuth|Не подключено|needs_config|Требуется/);
    expect(card.textContent).toMatch(/Microsoft/);
  });

  it("photo upload control exists", async () => {
    mount();
    expect(await screen.findByTestId("lawyer-photo-input")).toBeTruthy();
  });

  it("shows archive filters", async () => {
    mount("/workspace/legal?view=archive");
    const filters = await screen.findByTestId("lawyer-archive-filters");
    expect(filters.textContent).toMatch(/Дела/);
    expect(filters.textContent).toMatch(/Договоры/);
    expect(filters.textContent).toMatch(/Документы/);
    expect(filters.textContent).toMatch(/События/);
  });
});
