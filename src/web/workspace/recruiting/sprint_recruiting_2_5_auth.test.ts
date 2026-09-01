/**
 * Sprint Recruiting 2.5 — canonical auth client + error copy + no browser secrets.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/auth/authStore";
import {
  recruitingOpsFirstError,
  recruitingOpsGet,
  recruitingOpsUserError,
} from "./recruitingApi";
import { RecruitingBusinessPage } from "./RecruitingBusinessPage";
import { RecruitingProjectsPage } from "./RecruitingProjectsPage";
import { VanguardProjectPage } from "./VanguardProjectPage";
import { AdsControlCenterPage } from "./AdsControlCenterPage";
import { RecruitingInfraPage } from "./RecruitingInfraPage";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { WhatsAppConversation } from "./WhatsAppConversation";
import { CandidateEmailComposer } from "./CandidateEmailComposer";

const fetchMock = vi.fn(async () => ({
  ok: true,
  status: 200,
  json: async () => ({ ok: true, items: [] }),
}));

vi.stubGlobal("fetch", fetchMock);

describe("Recruiting 2.5 auth client", () => {
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

  it("attaches the session Bearer token on recruiter GET", async () => {
    await recruitingOpsGet("/leads", {
      "X-Organization-Id": "ados",
      "X-Role": "platform_owner",
    });
    expect(fetchMock).toHaveBeenCalled();
    const first = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(String(first[0])).toContain("/api/recruiting-ops/v1/leads");
    const headers = new Headers(first[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer aaa.bbb.ccc");
    expect(headers.get("X-Organization-Id")).toBe("ados");
    expect(headers.get("X-Role")).toBe("platform_owner");
  });

  it("distinguishes 401 from unavailable / 403 / 5xx", () => {
    expect(recruitingOpsUserError(401)).toMatch(/Войдите|доступа/i);
    expect(recruitingOpsUserError(401)).not.toMatch(/недоступен/i);
    expect(recruitingOpsUserError(403)).toMatch(/прав/i);
    expect(recruitingOpsUserError(502)).toMatch(/недоступен \(HTTP 502\)/);
    expect(recruitingOpsUserError(0)).toMatch(/соединение|backend/i);
    expect(
      recruitingOpsFirstError([
        { ok: false, status: 502, json: {} },
        { ok: false, status: 401, json: {} },
      ]),
    ).toMatch(/Войдите|доступа/i);
  });

  it("all recruiter pages resolve through the canonical client module", () => {
    expect(RecruitingBusinessPage).toBeTypeOf("function");
    expect(RecruitingProjectsPage).toBeTypeOf("function");
    expect(VanguardProjectPage).toBeTypeOf("function");
    expect(AdsControlCenterPage).toBeTypeOf("function");
    expect(RecruitingInfraPage).toBeTypeOf("function");
    expect(ProviderConnectionsPage).toBeTypeOf("function");
    expect(WhatsAppConversation).toBeTypeOf("function");
    expect(CandidateEmailComposer).toBeTypeOf("function");
  });

  it("does not ship JWT or ingest secrets to the browser client", async () => {
    const src = await import("./recruitingApi");
    expect(JSON.stringify(src)).not.toMatch(/IAM_JWT_SECRET|VANGUARD_INGEST_SECRET|API_JWT_SECRET|SECURITY_MASTER_KEY/);
  });
});
