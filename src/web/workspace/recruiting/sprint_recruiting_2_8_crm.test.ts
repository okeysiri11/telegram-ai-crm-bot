/**
 * Sprint Recruiting 2.8 — CRM mutations keep production relative Recruiting Ops URLs.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/auth/authStore";
import {
  recruitingOpsPost,
  recruitingWorkspaceHeaders,
  resolveRecruitingOpsPrefix,
} from "./recruitingApi";

const fetchMock = vi.fn(async () => ({
  ok: true,
  status: 200,
  json: async () => ({ ok: true, item: { id: "x", status: "qualified" } }),
}));

vi.stubGlobal("fetch", fetchMock);

describe("Recruiting 2.8 CRM relative API routing", () => {
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

  it("status, vacancy, convert, and stage posts stay same-origin", async () => {
    expect(resolveRecruitingOpsPrefix("http://localhost:8080/api/recruiting-ops/v1", { prod: true })).toBe(
      "/api/recruiting-ops/v1",
    );
    const headers = recruitingWorkspaceHeaders("demo-corp", "platform_owner");
    for (const path of [
      "/leads/lead-1/status",
      "/leads/lead-1/vacancy",
      "/leads/lead-1/convert",
      "/vacancies/vac-1",
      "/candidates/cand-1/stage",
    ]) {
      fetchMock.mockClear();
      await recruitingOpsPost(path, { status: "qualified" }, headers);
      const first = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
      expect(String(first[0])).toBe(`/api/recruiting-ops/v1${path}`);
      expect(String(first[0])).not.toMatch(/localhost|127\.0\.0\.1|:8080/i);
    }
  });
});
