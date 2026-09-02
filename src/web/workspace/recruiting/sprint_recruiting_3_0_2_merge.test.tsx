/**
 * Sprint Recruiting 3.0.2 — duplicate badge, merge comparison, preview, confirm.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";

type Row = Record<string, unknown>;

const vacancies = [{ id: "vac-1", title: "Дронщик", status: "open" }];
let candidates: Row[] = [];
let mergeConflict = false;
let lastMergeBody: Record<string, unknown> | null = null;

function seedDuplicates() {
  candidates = [
    {
      id: "cand-1",
      name: "timofii",
      email: "timofiikarpenchuk@gmail.com",
      phone: "37281093104",
      assignee: "recruiter.owner",
      pipeline_stage: "APPROVED",
      vacancy: "дронщик",
      source: "google",
      possible_duplicate: true,
      duplicate_candidate_ids: ["cand-2"],
      lead_ids: ["lead-1"],
      applications: [{ lead_id: "lead-1", source: "google", created_at: "2026-08-01T00:00:00Z" }],
      created_at: "2026-08-01T00:00:00Z",
    },
    {
      id: "cand-2",
      name: "timofii",
      email: "timofiikarpenchuk@gmail.com",
      phone: "+372 810 93104",
      assignee: "recruiter.owner",
      pipeline_stage: "QUALIFIED",
      vacancy: "логист",
      source: "meta",
      possible_duplicate: true,
      duplicate_candidate_ids: ["cand-1"],
      lead_ids: ["lead-2"],
      applications: [{ lead_id: "lead-2", source: "meta", created_at: "2026-08-10T00:00:00Z" }],
      created_at: "2026-08-10T00:00:00Z",
    },
  ];
}

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  const method = String(init?.method || "GET").toUpperCase();
  if (method === "POST" && u.includes("/candidates/") && u.includes("/merge")) {
    lastMergeBody = JSON.parse(String(init?.body || "{}")) as Record<string, unknown>;
    const preview = {
      name: "timofii",
      application_count: 2,
      lead_count: 2,
      pipeline_stage: "APPROVED",
      assignee: "recruiter.owner",
      source_count: 2,
    };
    if (lastMergeBody.preview) {
      return { ok: true, status: 200, json: async () => ({ ok: true, preview, safety: "match", comparison: {} }) };
    }
    if (mergeConflict) {
      return {
        ok: false,
        status: 409,
        json: async () => ({ ok: false, error: "conflict", safety: "ambiguous", message_ru: "Идентичность неоднозначна" }),
      };
    }
    candidates = [
      {
        ...candidates[0],
        possible_duplicate: false,
        duplicate_candidate_ids: [],
        lead_ids: ["lead-1", "lead-2"],
        applications: [
          { lead_id: "lead-1", source: "google" },
          { lead_id: "lead-2", source: "meta" },
        ],
        pipeline_stage: "APPROVED",
      },
    ];
    return { ok: true, status: 200, json: async () => ({ ok: true, item: candidates[0], preview, already_merged: false, safety: "match" }) };
  }
  if (u.includes("/dashboard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        cards: { candidates: candidates.length, leads: 2, interviews: 0, hired: 0 },
        recruiters: [],
        attention_items: [],
        overdue_tasks: [],
        next_tasks: [],
        visits: { message_ru: "Нет данных о посещениях" },
        projects: [],
      }),
    };
  }
  if (u.includes("/vacancies")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: vacancies }) };
  }
  if (u.includes("/candidates")) {
    const approved = candidates.filter((c) => c.pipeline_stage === "APPROVED");
    const qualified = candidates.filter((c) => c.pipeline_stage === "QUALIFIED");
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: candidates,
        pipeline: { NEW: [], QUALIFIED: qualified, INTERVIEW: [], APPROVED: approved, HIRED: [], REJECTED: [] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path = "/workspace/recruiting?view=candidates") {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/recruiting" element={<RecruitingBusinessPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint Recruiting 3.0.2 merge UI", () => {
  beforeEach(() => {
    fetchMock.mockClear();
    lastMergeBody = null;
    mergeConflict = false;
    seedDuplicates();
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

  it("shows duplicate badge and merge action", async () => {
    mount();
    const badges = await screen.findAllByTestId("duplicate-badge-cand-1");
    expect(badges.length).toBeGreaterThan(0);
    expect(screen.getAllByTestId("merge-candidates-cand-1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Возможный дубль").length).toBeGreaterThan(0);
  });

  it("opens comparison, preview, confirms, refreshes list and pipeline", async () => {
    mount("/workspace/recruiting?view=candidates");
    fireEvent.click((await screen.findAllByTestId("merge-candidates-cand-1"))[0]);
    expect(await screen.findByTestId("candidate-merge-panel")).toBeTruthy();
    expect(screen.getByTestId("merge-comparison")).toBeTruthy();
    expect(screen.getByText("Кандидат 1")).toBeTruthy();
    expect(screen.getByText("Кандидат 2")).toBeTruthy();
    expect(await screen.findByTestId("merge-preview")).toBeTruthy();
    expect(screen.getByText("После объединения")).toBeTruthy();
    expect(screen.getByTestId("merge-cancel")).toBeTruthy();
    fireEvent.click(screen.getByTestId("merge-confirm"));
    expect(await screen.findByTestId("merge-success")).toBeTruthy();
    await waitFor(() => expect(candidates).toHaveLength(1));
    await waitFor(() => expect(screen.queryByTestId("duplicate-badge-cand-1")).toBeNull());
    mount("/workspace/recruiting?view=pipeline");
    expect(await screen.findByTestId("recruiting-pipeline-board")).toBeTruthy();
    expect(screen.getByTestId("pipeline-card-cand-1")).toBeTruthy();
    expect(screen.queryByTestId("pipeline-card-cand-2")).toBeNull();
  });

  it("shows conflict state", async () => {
    mergeConflict = true;
    mount();
    fireEvent.click((await screen.findAllByTestId("merge-candidates-cand-1"))[0]);
    await screen.findByTestId("merge-preview");
    fireEvent.click(screen.getByTestId("merge-confirm"));
    expect(await screen.findByTestId("merge-conflict")).toBeTruthy();
    expect(screen.getByText(/неоднозначна/i)).toBeTruthy();
    expect(candidates).toHaveLength(2);
  });
});
