/**
 * Sprint Lawyer 3.3 — Monitoring nav / providers UI.
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
          cards: { clients: 0, open_cases: 0, hearings_today: 0, open_deadlines: 0, pending_approvals: 0 },
          google_calendar: { status: "needs_config" },
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
            { provider: "ua_edrsr", label_ru: "ЄДРСР", status: "UNAVAILABLE", message_ru: "недоступна", official_source: "reyestr" },
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

describe("Sprint Lawyer 3.3 Monitoring", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("shows Мониторинг in nav", async () => {
    mount();
    const root = await screen.findByTestId("lawyer-business-cabinet");
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent || "").toMatch(/Мониторинг/);
  });

  it("monitoring panel tabs and sources", async () => {
    mount("/workspace/legal?view=monitoring");
    expect(await screen.findByTestId("lawyer-monitoring-panel")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-monitoring-tabs")).toBeTruthy();
  });
});
