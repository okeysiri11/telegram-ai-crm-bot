/**
 * Sprint Lawyer 3.1 — CRM cardoteka / task views / filters.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
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
            { provider: "microsoft", label_ru: "Microsoft Calendar", status: "coming_soon" },
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

describe("Sprint Lawyer 3.1 CRM", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("shows client filters", async () => {
    mount("/workspace/legal?view=clients");
    expect(await screen.findByTestId("lawyer-client-filters")).toBeTruthy();
  });

  it("shows task views", async () => {
    mount("/workspace/legal?view=tasks");
    const views = await screen.findByTestId("lawyer-task-views");
    expect(views.textContent).toMatch(/Сегодня/);
    expect(views.textContent).toMatch(/Просроченные/);
  });

  it("calendar month still present", async () => {
    mount("/workspace/legal?view=calendar");
    expect(await screen.findByTestId("lawyer-calendar-month")).toBeTruthy();
  });
});
