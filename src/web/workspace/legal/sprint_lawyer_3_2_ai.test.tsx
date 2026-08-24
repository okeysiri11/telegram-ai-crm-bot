/**
 * Sprint Lawyer 3.2 — AI analysis / AI lawyer workspace UI.
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
    if (u.includes("/ai/catalog") || u.includes("/ai/actions")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          actions: [{ id: "summarize", label_ru: "Кратко объяснить" }],
          modes: [{ id: "consult", label_ru: "Консультация" }, { id: "draft_document", label_ru: "Создать документ" }],
        }),
      };
    }
    if (u.includes("/ai/analyses")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    }
    if (u.includes("/integrations/calendars")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          items: [{ provider: "google", label_ru: "Google Calendar", status: "needs_config" }],
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

describe("Sprint Lawyer 3.2 AI workspace", () => {
  beforeEach(() => {
    (fetch as unknown as { mockClear: () => void }).mockClear?.();
  });

  it("nav splits AI-анализ and AI-юрист", async () => {
    mount();
    const root = await screen.findByTestId("lawyer-business-cabinet");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/AI-анализ/);
    expect(nav).toMatch(/AI-юрист/);
    expect(nav).toMatch(/История AI/);
  });

  it("AI-анализ panel shows actions and attach", async () => {
    mount("/workspace/legal?view=ai-analysis");
    expect(await screen.findByTestId("lawyer-ai-analysis-panel")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-ai-actions")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-ai-attach")).toBeTruthy();
  });

  it("AI-юрист panel shows context and run", async () => {
    mount("/workspace/legal?view=ai");
    expect(await screen.findByTestId("lawyer-ai-lawyer-panel")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-ai-lawyer-context")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-ai-lawyer-run")).toBeTruthy();
    expect(await screen.findByTestId("lawyer-ai-context-inspector")).toBeTruthy();
  });
});
