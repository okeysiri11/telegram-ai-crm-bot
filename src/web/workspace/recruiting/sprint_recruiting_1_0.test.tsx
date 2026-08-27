/**
 * Sprint Recruiting 1.0 — recruiting cabinet UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        item: { id: "lead-1", name: "Анна", status: "new", pipeline_stage: "NEW" },
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { leads: 0, candidates: 0, overdue_tasks: 1, next_tasks: 1 },
        overdue_tasks: [{ id: "t1", title: "Позвонить", due_date: "2020-01-01", status: "open" }],
        next_tasks: [{ id: "t2", title: "Провести интервью", due_date: "2099-01-01", status: "open" }],
        visits: { available: false, message_ru: "Нет данных о посещениях" },
        attention: [{ kind: "overdue_tasks", message_ru: "Просрочено задач: 1" }],
      }),
    };
  }
  if (u.includes("/analytics")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        visits: { available: false, message_ru: "Нет данных о посещениях", count: null },
        funnel: { leads: 0, qualified: 0, interviews: 0, approved: 0, hired: 0 },
        by_source: [],
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path = "/workspace/recruiting") {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/recruiting" element={<RecruitingBusinessPage />} />
        <Route path="/workspace/recruiting/:sub" element={<RecruitingBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint Recruiting 1.0 cabinet", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("renders RU operational nav and overdue/next tasks", async () => {
    mount();
    const root = await screen.findByTestId("recruiting-business-cabinet");
    expect(root).toBeTruthy();
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Проекты/);
    expect(nav).toMatch(/Лиды/);
    expect(nav).toMatch(/Кандидаты/);
    expect(nav).toMatch(/Вакансии/);
    expect(nav).toMatch(/Воронка/);
    expect(nav).toMatch(/Кампании/);
    expect(nav).toMatch(/Задачи/);
    expect(nav).toMatch(/Аналитика/);
    expect(await screen.findByTestId("recruiting-header-context")).toBeTruthy();
    expect(root.textContent).toMatch(/Просрочено/);
    expect(root.textContent).toMatch(/Ближайшие задачи/);
    expect(root.textContent).toMatch(/Позвонить/);
    expect(root.textContent).toMatch(/Провести интервью/);
    expect((await screen.findByTestId("recruiting-visits-empty")).textContent).toMatch(/Нет данных о посещениях/);
  });

  it("creates a lead through Recruiting Ops API", async () => {
    mount("/workspace/recruiting?view=leads");
    await screen.findByTestId("recruiting-business-cabinet");
    fireEvent.click(await screen.findByRole("button", { name: /Создать лид/i }));
    const form = await screen.findByTestId("recruiting-lead-form");
    const nameInput = form.querySelector("input");
    fireEvent.change(nameInput!, { target: { value: "Анна" } });
    fireEvent.click(screen.getByTestId("recruiting-lead-submit"));
    await waitFor(() => {
      const posts = fetchMock.mock.calls.filter((c) => String(c[1]?.method || "").toUpperCase() === "POST");
      expect(posts.some((c) => String(c[0]).includes("/api/recruiting-ops/v1/leads"))).toBe(true);
    });
  });

  it("shows visit-unavailable copy on analytics", async () => {
    mount("/workspace/recruiting?view=analytics");
    expect((await screen.findByTestId("recruiting-analytics-visits")).textContent).toMatch(/Нет данных о посещениях/);
  });
});
