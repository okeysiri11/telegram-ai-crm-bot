/**
 * Sprint Recruiting 2.9 — lead → recruiter → candidate workflow UX.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";
import { LEAD_STATUS_CHOICES, canSelectLeadStatus } from "./recruitingWorkflow";

type Lead = Record<string, unknown>;
type Candidate = Record<string, unknown>;

const leads: Lead[] = [
  {
    id: "lead-a",
    name: "Анна Коваль",
    email: "twins@example.com",
    phone: "+380501111111",
    status: "new",
    assignee: "",
    vacancy_id: "",
    source: "vanguard",
    created_at: "2026-09-01T08:00:00Z",
  },
  {
    id: "lead-b",
    name: "Богдан Коваль",
    email: "twins@example.com",
    phone: "+380501111111",
    status: "new",
    assignee: "Timofii",
    vacancy_id: "",
    source: "vanguard",
    created_at: "2026-09-01T09:00:00Z",
  },
];

const vacancies = [{ id: "vac-1", title: "Логист Vanguard", status: "open" }];
const candidates: Candidate[] = [];
let convertStarted = false;

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  const method = String(init?.method || "GET").toUpperCase();
  if (method === "POST") {
    const body = JSON.parse(String(init?.body || "{}")) as Record<string, unknown>;
    if (u.includes("/leads/lead-a/assign")) {
      leads[0] = { ...leads[0], assignee: body.assignee || "" };
      return { ok: true, status: 200, json: async () => ({ ok: true, item: leads[0] }) };
    }
    if (u.includes("/leads/lead-a/vacancy")) {
      leads[0] = { ...leads[0], vacancy_id: body.vacancy_id, vacancy: "Логист Vanguard" };
      return { ok: true, status: 200, json: async () => ({ ok: true, item: leads[0] }) };
    }
    if (u.includes("/leads/lead-a/qualify") || (u.includes("/leads/lead-a/status") && body.status === "qualified")) {
      leads[0] = { ...leads[0], status: "qualified" };
      return { ok: true, status: 200, json: async () => ({ ok: true, item: leads[0] }) };
    }
    if (u.includes("/leads/lead-a/convert")) {
      if (candidates.length || convertStarted || leads[0]?.candidate_id) {
        const existing = candidates[0] || { id: leads[0]?.candidate_id };
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, already_converted: true, duplicate: true, item: existing }),
        };
      }
      convertStarted = true;
      const created = {
        id: "cand-a",
        lead_id: "lead-a",
        name: leads[0]?.name,
        email: leads[0]?.email,
        phone: leads[0]?.phone,
        pipeline_stage: "QUALIFIED",
        source: "vanguard",
        assignee: leads[0]?.assignee,
        vacancy_id: leads[0]?.vacancy_id,
      };
      candidates.splice(0, candidates.length, created);
      leads[0] = { ...leads[0], status: "converted", candidate_id: "cand-a" };
      return { ok: true, status: 201, json: async () => ({ ok: true, item: created }) };
    }
    if (u.includes("/candidates/cand-a/stage")) {
      candidates[0] = { ...candidates[0], pipeline_stage: body.pipeline_stage };
      return { ok: true, status: 200, json: async () => ({ ok: true, item: candidates[0] }) };
    }
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "x" } }) };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { new_leads: 2, qualified: 0, candidates: candidates.length, interviews: 0, hired: 0, leads: 2 },
        recruiters: [{ id: "Timofii", label: "Timofii" }],
        attention_items: [
          { kind: "unassigned", entity_type: "lead", entity_id: "lead-a", message_ru: "Лид без ответственного: Анна Коваль" },
        ],
        attention: [],
        overdue_tasks: [],
        next_tasks: [],
        visits: { message_ru: "Нет данных о посещениях" },
        projects: [{ project_key: "vanguard", name: "Vanguard", new_leads: 2 }],
      }),
    };
  }
  if (u.includes("/leads")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: leads }) };
  }
  if (u.includes("/vacancies")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: vacancies }) };
  }
  if (u.includes("/candidates")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: candidates,
        pipeline: { NEW: [], QUALIFIED: candidates, INTERVIEW: [], APPROVED: [], HIRED: [], REJECTED: [] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path = "/workspace/recruiting?view=leads&id=lead-a") {
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

describe("Sprint Recruiting 2.9 workflow UX", () => {
  beforeEach(() => {
    fetchMock.mockClear();
    leads[0] = { ...leads[0], status: "new", assignee: "", vacancy_id: "", candidate_id: null };
    leads[1] = { ...leads[1], status: "new", assignee: "Timofii" };
    candidates.splice(0, candidates.length);
    convertStarted = false;
    useRoleSwitcher.setState({ activeRoleId: "owner" });
    useAuthStore.setState({
      accessToken: "aaa.bbb.ccc",
      refreshToken: "r",
      authMode: "platform_jwt",
      user: {
        id: "owner-1",
        email: "owner@demo.corp",
        name: "Owner",
        tenantId: "ados",
        roleId: "platform_owner",
        roles: ["owner"],
        permissions: ["read", "write", "admin"],
      },
    });
  });

  it("renders one recruiter/vacancy panel and independent same-email leads", async () => {
    mount();
    const panel = await screen.findByTestId("lead-workflow-panel");
    expect(panel).toBeTruthy();
    expect(screen.getAllByTestId("lead-workflow-panel")).toHaveLength(1);
    expect(screen.getByTestId("lead-recruiter-select")).toBeTruthy();
    expect(screen.getByTestId("lead-vacancy-select")).toBeTruthy();
    expect(within(screen.getByTestId("lead-recruiter-select")).getByText("Timofii")).toBeTruthy();
    expect(screen.queryAllByRole("button", { name: /Назначить / }).length).toBe(0);
    expect(screen.getAllByTestId("lead-qualify")).toHaveLength(1);
    expect(screen.getByTestId("lead-workflow-name")).toHaveTextContent("Анна Коваль");
    expect(screen.getAllByText("Богдан Коваль").length).toBeGreaterThan(0);
    expect(LEAD_STATUS_CHOICES.some((item) => item.id === "converted")).toBe(false);
    expect(canSelectLeadStatus("converted")).toBe(false);
    const status = screen.getByTestId("lead-status-select") as HTMLSelectElement;
    expect([...status.options].map((o) => o.value)).not.toContain("converted");
  });

  it("persists recruiter, vacancy, qualify, convert idempotently and opens candidate", async () => {
    mount();
    await screen.findByTestId("lead-workflow-panel");
    fireEvent.change(screen.getByTestId("lead-recruiter-select"), { target: { value: "Timofii" } });
    await waitFor(() => {
      expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/leads/lead-a/assign"))).toBe(true);
    });
    expect(await screen.findByTestId("lead-workflow-success", {}, { timeout: 5000 })).toHaveTextContent(/Ответственный сохранён/);
    fireEvent.change(screen.getByTestId("lead-vacancy-select"), { target: { value: "vac-1" } });
    await waitFor(() => expect(screen.getByTestId("lead-workflow-success")).toHaveTextContent(/Вакансия сохранена/));
    fireEvent.click(screen.getByTestId("lead-qualify"));
    await waitFor(() => expect(leads[0]?.status).toBe("qualified"));
    fireEvent.click(screen.getByTestId("lead-convert"));
    fireEvent.click(screen.getByTestId("lead-convert"));
    await waitFor(() => expect(screen.getByTestId("lead-open-candidate")).toBeTruthy());
    expect(candidates).toHaveLength(1);
    fireEvent.click(screen.getByTestId("lead-open-candidate"));
    expect(await screen.findByTestId("candidate-workflow-panel")).toBeTruthy();
    expect(screen.getByTestId("candidate-open-lead")).toBeTruthy();
    expect(screen.getByTestId("candidate-source")).toHaveTextContent("Vanguard");
    fireEvent.click(screen.getByTestId("candidate-stage-INTERVIEW"));
    await waitFor(() => expect(candidates[0]?.pipeline_stage).toBe("INTERVIEW"));
  });

  it("hides mutate actions for observer", async () => {
    useRoleSwitcher.setState({ activeRoleId: "viewer" });
    mount();
    await screen.findByTestId("lead-workflow-panel");
    expect(screen.queryByTestId("lead-recruiter-select")).toBeNull();
    expect(screen.queryByTestId("lead-convert")).toBeNull();
    expect(screen.queryByTestId("lead-qualify")).toBeNull();
  });
});
