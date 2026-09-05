/**
 * Sprint Recruiting 3.1 — TEST badge, interview action, production analytics copy.
 */

import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";
import { isTestTraffic } from "./recruitingWorkflow";

const leads = [
  {
    id: "lead-real",
    name: "Анна Коваль",
    status: "new",
    source: "vanguard",
    traffic_class: "PRODUCTION",
  },
  {
    id: "lead-test",
    name: "E2E Candidate",
    status: "converted",
    source: "vanguard",
    utm_source: "e2e_test",
    utm_campaign: "vanguard_e2e",
    traffic_class: "TEST",
    candidate_id: "cand-test",
    assignee: "recruiter.ira",
  },
];

const candidates = [
  {
    id: "cand-test",
    name: "E2E Candidate",
    pipeline_stage: "QUALIFIED",
    utm_source: "e2e_test",
    traffic_class: "TEST",
    lead_id: "lead-test",
    assignee: "recruiter.ira",
  },
];

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  const method = String(init?.method || "GET").toUpperCase();
  if (method === "POST" && u.includes("/candidates/cand-test/interview")) {
    candidates[0] = { ...candidates[0], pipeline_stage: "INTERVIEW" };
    return { ok: true, status: 200, json: async () => ({ ok: true, interview_scheduled: true, item: candidates[0] }) };
  }
  if (method === "POST" && u.includes("/candidates/cand-test/assign")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, item: candidates[0] }) };
  }
  if (u.includes("/analytics")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        visits: { available: false, message_ru: "Нет данных о посещениях" },
        funnel: { leads: 1, qualified: 1, interviews: 0, approved: 0, hired: 0 },
        by_source: [{ id: "vanguard", label: "vanguard", count: 1 }],
        traffic: { production_only: true, excluded_test_leads: 1, excluded_test_candidates: 1 },
      }),
    };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { leads: 2, candidates: 1 },
        visits: { available: false, message_ru: "Нет данных о посещениях" },
        attention: [],
      }),
    };
  }
  if (u.includes("/leads")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: leads }) };
  }
  if (u.includes("/candidates")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: candidates, pipeline: { QUALIFIED: candidates } }) };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

const originalFetch = globalThis.fetch;
vi.stubGlobal("fetch", fetchMock);

function mount(path: string) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/recruiting" element={<RecruitingBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint Recruiting 3.1 pipeline UX", () => {
  afterAll(() => {
    globalThis.fetch = originalFetch;
  });

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockClear();
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
    } as never);
  });

  it("marks TEST traffic without treating production leads as test", () => {
    expect(isTestTraffic({ utm_source: "e2e_test", utm_campaign: "vanguard_e2e" })).toBe(true);
    expect(isTestTraffic({ utm_source: "instagram", utm_campaign: "vanguard_pre_ads_test" })).toBe(true);
    expect(isTestTraffic({ source: "vanguard", traffic_class: "PRODUCTION" })).toBe(false);
  });

  it("shows TEST badge on e2e leads only", async () => {
    mount("/workspace/recruiting?view=leads");
    expect((await screen.findAllByText(/E2E Candidate · TEST/)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Анна Коваль · TEST/)).toBeNull();
  });

  it("shows excluded TEST copy on analytics", async () => {
    mount("/workspace/recruiting?view=analytics");
    expect((await screen.findByTestId("recruiting-analytics-test-excluded")).textContent).toMatch(/TEST-трафик исключён/);
  });

  it("schedules interview through the dedicated action", async () => {
    mount("/workspace/recruiting?view=candidates&id=cand-test");
    fireEvent.click(await screen.findByTestId("candidate-schedule-interview"));
    await waitFor(() => {
      expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/candidates/cand-test/interview"))).toBe(true);
    });
  });
});
