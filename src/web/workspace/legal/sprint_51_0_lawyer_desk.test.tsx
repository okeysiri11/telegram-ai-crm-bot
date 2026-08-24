/**
 * Sprint 51.0 — Lawyer Operator Desk cabinet UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LawyerBusinessPage } from "./LawyerBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        item: { id: "new-1", name: "Test", title: "Test", status: "active" },
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { clients: 0, open_cases: 0, hearings_today: 1, open_deadlines: 2, pending_approvals: 0 },
        google_calendar: { status: "needs_config" },
      }),
    };
  }
  if (u.includes("/integrations/google-calendar")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({ status: "needs_config", message_ru: "OAuth не настроен" }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path = "/workspace/legal") {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/legal" element={<LawyerBusinessPage />} />
        <Route path="/workspace/legal/:sub" element={<LawyerBusinessPage />} />
        <Route path="/workspace/legal/pilot" element={<div>pilot</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 51.0 Lawyer desk", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders RU nav sections and header context", async () => {
    mount();
    const root = await screen.findByTestId("lawyer-business-cabinet");
    expect(root).toBeTruthy();
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Клиенты/);
    expect(nav).toMatch(/Дела/);
    expect(nav).toMatch(/Договоры/);
    expect(nav).toMatch(/Документы/);
    expect(nav).toMatch(/Задачи\/Сроки/);
    expect(nav).toMatch(/Суды\/Заседания/);
    expect(nav).toMatch(/Календарь/);
    expect(nav).toMatch(/AI-юрист/);
    expect(nav).toMatch(/AI-анализ/);
    expect(nav).toMatch(/Мониторинг/);
    expect(nav).toMatch(/Активность/);
    expect(await screen.findByTestId("lawyer-header-context")).toBeTruthy();
    expect(root.textContent).toMatch(/Заседания сегодня/);
    expect(root.textContent).toMatch(/Открытые сроки/);
  });

  it("primary CTAs open create forms that POST to legal-ops", async () => {
    mount();
    await screen.findByTestId("lawyer-business-cabinet");
    const createClient = await screen.findByRole("button", { name: /Создать клиента/i });
    fireEvent.click(createClient);
    const form = await screen.findByTestId("lawyer-client-form");
    expect(form).toBeTruthy();
    const nameInput = form.querySelector("input");
    expect(nameInput).toBeTruthy();
    fireEvent.change(nameInput!, { target: { value: "Петров" } });
    fireEvent.click(screen.getByTestId("lawyer-client-submit"));
    await waitFor(() => {
      const posts = fetchMock.mock.calls.filter((c) => String(c[1]?.method || "").toUpperCase() === "POST");
      expect(posts.some((c) => String(c[0]).includes("/api/legal-ops/v1/clients"))).toBe(true);
    });
  });

  it("dashboard cards render workload strip", async () => {
    mount();
    const root = await screen.findByTestId("lawyer-business-cabinet");
    await waitFor(() => {
      expect(root.textContent).toMatch(/Заседания сегодня/);
      expect(root.textContent).toMatch(/Ожидают согласования/);
    });
  });
});
