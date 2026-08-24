/**
 * Sprint Lawyer 3.5 — calendar filters, settings sources, attachments actions.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LawyerBusinessPage } from "./LawyerBusinessPage";
import { LawyerCalendarBoard } from "./LawyerCalendarBoard";

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
          cards: { clients: 0, open_cases: 0, hearings_today: 0, open_deadlines: 0, pending_approvals: 0 },
          google_calendar: { status: "needs_config" },
        }),
      };
    }
    if (u.includes("/integrations/health")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [
            { id: "google_calendar", label_ru: "Google Calendar", icon: "yellow", status_label_ru: "Не настроен администратором" },
            { id: "scheduler", label_ru: "Scheduler", icon: "green", status_label_ru: "Подключено" },
          ],
          errors_24h_count: 0,
        }),
      };
    }
    if (u.includes("/integrations/google-calendar")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, status: "needs_config" }) };
    }
    if (u.includes("/monitoring/") || u.includes("/providers") || u.includes("/ai/")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [], actions: [], modes: [] }) };
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

describe("Sprint Lawyer 3.5", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("settings shows Источники данных", async () => {
    mount("/workspace/legal?view=settings");
    expect(await screen.findByTestId("lawyer-settings-sources")).toBeTruthy();
    expect(screen.getByText(/Ручной импорт/)).toBeTruthy();
  });

  it("calendar has month/week/day and contract filter", () => {
    render(
      <LawyerCalendarBoard
        events={[
          {
            id: "1",
            title: "Срок договора",
            event_type: "contract_end",
            starts_at: "2026-08-12T10:00:00+00:00",
          },
        ]}
        canCreate
        onCreate={() => undefined}
        onOpen={() => undefined}
        onEdit={() => undefined}
        onArchive={() => undefined}
      />,
    );
    expect(screen.getByTestId("lawyer-calendar-filters").textContent).toMatch(/Договоры/);
    expect(screen.getByText("Месяц")).toBeTruthy();
    expect(screen.getByText("Неделя")).toBeTruthy();
    expect(screen.getByText("День")).toBeTruthy();
  });
});
