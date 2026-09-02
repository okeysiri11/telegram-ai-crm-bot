/**
 * Sprint Recruiting 2.10 — converted lead CTA and terminal pipeline UX.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";

const fetchMock = vi.fn(async (url: string) => {
  const u = String(url);
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: {},
        recruiters: [],
        attention_items: [],
        overdue_tasks: [],
        next_tasks: [],
        visits: { message_ru: "Нет данных о посещениях" },
        projects: [],
      }),
    };
  }
  if (u.includes("/leads")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            id: "lead-converted",
            name: "Timofii",
            email: "timofiikarpenchuk@gmail.com",
            phone: "37281093104",
            status: "converted",
            candidate_id: "cand-1",
            source: "vanguard",
          },
        ],
      }),
    };
  }
  if (u.includes("/candidates")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            id: "cand-hired",
            name: "Hired Person",
            pipeline_stage: "HIRED",
            lead_id: "lead-converted",
            lead_ids: ["lead-converted", "lead-2"],
            applications: [{ lead_id: "lead-converted" }, { lead_id: "lead-2" }],
            assignee: "recruiter.owner",
            vacancy: "дронщик",
          },
          {
            id: "cand-rejected",
            name: "Rejected Person",
            pipeline_stage: "REJECTED",
            lead_ids: ["lead-r"],
            applications: [{ lead_id: "lead-r" }],
          },
        ],
        pipeline: {
          NEW: [],
          QUALIFIED: [],
          INTERVIEW: [],
          APPROVED: [],
          HIRED: [{ id: "cand-hired", name: "Hired Person", pipeline_stage: "HIRED", assignee: "recruiter.owner", vacancy: "дронщик", lead_ids: ["lead-converted", "lead-2"], applications: [{ lead_id: "lead-converted" }, { lead_id: "lead-2" }] }],
          REJECTED: [{ id: "cand-rejected", name: "Rejected Person", pipeline_stage: "REJECTED" }],
        },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

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

describe("Sprint Recruiting 2.10 identity UX", () => {
  beforeEach(() => {
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
    });
  });

  it("converted lead shows Open Candidate and never Create Candidate", async () => {
    mount("/workspace/recruiting?view=leads&id=lead-converted");
    expect(await screen.findByTestId("lead-open-candidate")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Создать кандидата/i })).toBeNull();
    expect(screen.queryByTestId("lead-convert")).toBeNull();
  });

  it("hides pipeline Next on HIRED and REJECTED", async () => {
    mount("/workspace/recruiting?view=pipeline");
    expect(await screen.findByTestId("recruiting-pipeline-board")).toBeTruthy();
    expect(screen.queryByTestId("pipeline-next-cand-hired")).toBeNull();
    expect(screen.queryByTestId("pipeline-next-cand-rejected")).toBeNull();
    expect(screen.queryByRole("button", { name: "Дальше" })).toBeNull();
    expect(screen.getByText("2 заявки")).toBeTruthy();
    expect(screen.getByText("Owner")).toBeTruthy();
    expect(screen.getByText("дронщик")).toBeTruthy();
  });
});
