/**
 * Sprint Recruiting 2.7 — production same-origin API URL + honest errors.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/auth/authStore";
import {
  recruitingOpsGet,
  recruitingOpsPrefix,
  recruitingOpsUserError,
  recruitingReadOrganizationId,
  recruitingWorkspaceHeaders,
  resolveRecruitingOpsPrefix,
} from "./recruitingApi";

const fetchMock = vi.fn(async () => ({
  ok: true,
  status: 200,
  json: async () => ({ ok: true, items: [] }),
}));

vi.stubGlobal("fetch", fetchMock);

describe("Recruiting 2.7 production API resolution", () => {
  beforeEach(() => {
    fetchMock.mockClear();
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

  it("production prefix never contains localhost", () => {
    expect(resolveRecruitingOpsPrefix("/api/recruiting-ops/v1", { prod: true })).toBe("/api/recruiting-ops/v1");
    expect(resolveRecruitingOpsPrefix("http://127.0.0.1:8080/api/recruiting-ops/v1", { prod: true })).toBe(
      "/api/recruiting-ops/v1",
    );
    expect(resolveRecruitingOpsPrefix("http://localhost:8080/api/recruiting-ops/v1", { prod: true })).toBe(
      "/api/recruiting-ops/v1",
    );
    expect(recruitingOpsPrefix()).not.toMatch(/localhost|127\.0\.0\.1|:8080/i);
  });

  it("development may keep an explicit local origin", () => {
    expect(resolveRecruitingOpsPrefix("http://127.0.0.1:8080/api/recruiting-ops/v1", { prod: false })).toBe(
      "http://127.0.0.1:8080/api/recruiting-ops/v1",
    );
  });

  it("Leads, Vacancies, and Candidates use the same-origin prefix", async () => {
    for (const path of ["/leads", "/vacancies", "/candidates"]) {
      fetchMock.mockClear();
      await recruitingOpsGet(path, recruitingWorkspaceHeaders("demo-corp", "platform_owner"));
      const first = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
      expect(String(first[0])).toBe(`/api/recruiting-ops/v1${path}`);
      expect(String(first[0])).not.toMatch(/localhost|127\.0\.0\.1/i);
      const headers = new Headers(first[1]?.headers);
      expect(headers.get("Authorization")).toBe("Bearer aaa.bbb.ccc");
      expect(headers.get("X-Recruiting-Organization-Id")).toBe("ados");
    }
  });

  it("keeps e77ed37 owner mapping and recruiter isolation", () => {
    expect(recruitingReadOrganizationId("demo-corp", "platform_owner")).toBe("ados");
    expect(recruitingReadOrganizationId("demo-corp", "recruiter")).toBe("demo-corp");
    expect(recruitingReadOrganizationId("globefly", "platform_owner")).toBe("globefly");
  });

  it("does not mention :8080 on production network/auth/server errors", () => {
    expect(recruitingOpsUserError(0)).not.toMatch(/8080/);
    expect(recruitingOpsUserError(0, { error: "timeout" })).toMatch(/ожидания/i);
    expect(recruitingOpsUserError(401)).toMatch(/Войдите|доступа/i);
    expect(recruitingOpsUserError(403)).toMatch(/прав/i);
    expect(recruitingOpsUserError(404)).toMatch(/не найден/i);
    expect(recruitingOpsUserError(500)).toMatch(/HTTP 500/);
  });
});
