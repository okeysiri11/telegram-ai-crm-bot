/**
 * Sprint Lawyer 3.4 — Integrations health + monitoring form.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LawyerBusinessPage } from "./LawyerBusinessPage";
import { LawyerMonitoringPanel } from "./LawyerMonitoringPanel";

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
          google_calendar: { status: "needs_config", message_ru: "Не настроен администратором" },
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
            {
              id: "google_calendar",
              label_ru: "Google Calendar",
              icon: "yellow",
              status_label_ru: "Не настроен администратором",
              message_ru: "Требуется OAuth",
            },
            {
              id: "court_data",
              label_ru: "Судебные данные",
              icon: "gray",
              status_label_ru: "Выключено / недоступно",
              message_ru: "Источник не подключен",
            },
            {
              id: "scheduler",
              label_ru: "Scheduler",
              icon: "green",
              status_label_ru: "Подключено",
            },
          ],
          errors_24h_count: 0,
        }),
      };
    }
    if (u.includes("/providers")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [
            { provider: "manual_import", label_ru: "Ручной ввод", status: "MANUAL", message_ru: "manual" },
            {
              provider: "ua_edrsr",
              label_ru: "ЄДРСР",
              status: "UNAVAILABLE",
              message_ru: "Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник данных.",
            },
          ],
        }),
      };
    }
    if (u.includes("/monitoring/")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    if (u.includes("/ai/")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, actions: [], modes: [], items: [] }) };
    }
    if (u.includes("/integrations/calendars")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    if (u.includes("/integrations/google-calendar")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, status: "needs_config", message_ru: "Не настроен администратором" }),
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

describe("Sprint Lawyer 3.4", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("settings shows integrations health", async () => {
    mount("/workspace/legal?view=settings");
    const health = await screen.findByTestId("lawyer-integrations-health");
    expect(health).toBeTruthy();
    expect(health.textContent || "").toMatch(/Не настроен администратором/);
  });

  it("manual watch form fields", async () => {
    render(
      <LawyerMonitoringPanel
        headers={{ "X-Organization-Id": "demo", "X-Role": "lawyer" }}
        canOperate
        cases={[]}
        clients={[]}
        onRefresh={() => undefined}
      />,
    );
    expect(await screen.findByTestId("lawyer-watch-form")).toBeTruthy();
    expect(screen.getByTestId("lawyer-watchlist-save")).toBeTruthy();
  });
});
