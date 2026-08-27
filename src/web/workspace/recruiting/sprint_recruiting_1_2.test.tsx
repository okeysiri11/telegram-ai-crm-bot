/**
 * Sprint Recruiting 1.2 — projects nav + Vanguard control center.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";
import { RecruitingProjectsPage } from "./RecruitingProjectsPage";
import { VanguardProjectPage } from "./VanguardProjectPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "lead-1", name: "Анна" } }) };
  }
  if (u.includes("/projects/vanguard/integration")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        overall: { code: "UNKNOWN", label_ru: "Нет данных" },
        website_status: { code: "UNKNOWN", label_ru: "Нет данных" },
        website: { name: "Vanguard", public_url: null, environment: "development" },
        stages: [
          { id: "website", label_ru: "Сайт Vanguard", code: "UNKNOWN", status_label_ru: "Нет данных" },
          { id: "vanguard_endpoint", label_ru: "Серверный endpoint Vanguard", code: "CONNECTED", status_label_ru: "Подключено" },
          { id: "recruiting_api", label_ru: "Recruiting API", code: "CONNECTED", status_label_ru: "Подключено" },
          { id: "database", label_ru: "База данных", code: "DEGRADED", status_label_ru: "Сбои" },
        ],
        last_success_at: null,
        last_error: null,
        last_check_at: "2026-08-27T00:00:00Z",
      }),
    };
  }
  if (u.includes("/projects/vanguard") && !u.includes("/projects/vanguard/")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        project: { project_key: "vanguard", name: "Vanguard" },
        cards: {
          new_leads: 1,
          candidates: 0,
          active_vacancies: 0,
          applications_today: 0,
          lead_to_candidate: null,
          last_application_at: null,
        },
        recent_leads: [{ id: "l1", name: "Анна", status: "new", external_id: "VG-TEST-1", source: "vanguard" }],
        pipeline: { NEW: 0, QUALIFIED: 0, INTERVIEW: 0, APPROVED: 0, HIRED: 0, REJECTED: 0 },
      }),
    };
  }
  if (u.includes("/projects") && !u.includes("/projects/vanguard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            project_key: "vanguard",
            name: "Vanguard",
            type_ru: "Recruiting website",
            leads: 1,
            candidates: 0,
            active_vacancies: 0,
            last_application_at: null,
            last_sync_at: null,
            website_status: { code: "UNKNOWN", label_ru: "Нет данных" },
            integration_status: { code: "UNKNOWN", label_ru: "Нет данных" },
          },
        ],
      }),
    };
  }
  if (u.includes("/lookup")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, found: false, items: [] }) };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { leads: 1, candidates: 0, overdue_tasks: 0, next_tasks: 0 },
        overdue_tasks: [],
        next_tasks: [],
        visits: { available: false, message_ru: "Нет данных о посещениях" },
        projects: [
          {
            project_key: "vanguard",
            name: "Vanguard",
            new_leads: 1,
            last_application_at: null,
            integration_status: { code: "UNKNOWN", label_ru: "Нет данных" },
          },
        ],
      }),
    };
  }
  if (u.includes("/leads")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [{ id: "l1", name: "Анна", source: "vanguard", project_key: "vanguard", external_id: "VG-TEST-1", status: "new" }],
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [], funnel: {}, visits: { message_ru: "Нет данных о посещениях" } }) };
});

vi.stubGlobal("fetch", fetchMock);

function routes() {
  return (
    <Routes>
      <Route path="/workspace/recruiting" element={<RecruitingBusinessPage />} />
      <Route path="/workspace/recruiting/projects" element={<RecruitingProjectsPage />} />
      <Route path="/workspace/recruiting/projects/:projectKey" element={<VanguardProjectPage />} />
      <Route path="/workspace/recruiting/:sub" element={<RecruitingBusinessPage />} />
    </Routes>
  );
}

function mount(path: string) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(<MemoryRouter initialEntries={[withEmbed]}>{routes()}</MemoryRouter>);
}

describe("Sprint Recruiting 1.2 projects", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("shows Проекты in recruiting navigation", async () => {
    mount("/workspace/recruiting");
    const root = await screen.findByTestId("recruiting-business-cabinet");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Проекты/);
    expect(nav).toMatch(/Главная/);
    expect(nav).toMatch(/Лиды/);
    expect(await screen.findByTestId("recruiting-projects-home")).toBeTruthy();
    expect(root.textContent).toMatch(/Открыть Vanguard/);
  });

  it("opens projects page with Vanguard card", async () => {
    mount("/workspace/recruiting/projects");
    expect(await screen.findByTestId("recruiting-projects-page")).toBeTruthy();
    expect(await screen.findByTestId("recruiting-project-card-vanguard")).toBeTruthy();
    expect(screen.getByText("Vanguard")).toBeTruthy();
    expect(screen.getByText(/Recruiting website/)).toBeTruthy();
  });

  it("opens Vanguard overview, leads and integration without fabricated visits", async () => {
    mount("/workspace/recruiting/projects/vanguard");
    expect(await screen.findByTestId("vanguard-project-page")).toBeTruthy();
    expect(await screen.findByTestId("vanguard-overview")).toBeTruthy();
    expect(screen.getByTestId("vanguard-relationship").textContent).toMatch(/Сайт Vanguard/);
    const tabs = screen.getByTestId("vanguard-tabs");
    fireEvent.click(within(tabs).getByRole("button", { name: "Лиды" }));
    expect(await screen.findByTestId("vanguard-leads")).toBeTruthy();
    fireEvent.click(within(tabs).getByRole("button", { name: "Интеграция" }));
    expect(await screen.findByTestId("vanguard-integration")).toBeTruthy();
    expect(screen.getByTestId("vanguard-integration").textContent).toMatch(/Сайт Vanguard/);
    fireEvent.click(within(tabs).getByRole("button", { name: "Аналитика" }));
    await waitFor(() => {
      expect(screen.getByTestId("vanguard-analytics").textContent).toMatch(/Нет данных/);
    });
  });
});
