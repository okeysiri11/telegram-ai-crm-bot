/**
 * Sprint 40.4 — ISAM session must survive soft refresh failure (no logout wipe).
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/auth/authStore";

vi.mock("@/auth/identityApi", async () => {
  const actual = await vi.importActual<typeof import("@/auth/identityApi")>("@/auth/identityApi");
  return {
    ...actual,
    refreshProductionSession: vi.fn(async () => {
      throw new Error("ISAM refresh unavailable");
    }),
    productionLogin: vi.fn(),
    productionGoogleLogin: vi.fn(),
    productionRegister: vi.fn(),
    validateSessionOnline: vi.fn(async () => true),
  };
});

vi.mock("@/integrations/telemetry", () => ({
  telemetry: {
    audit: vi.fn(),
    pageView: vi.fn(),
    sessionStart: vi.fn(),
  },
}));

describe("Sprint 40.4 auth session persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: {
        id: "isam_id_1",
        email: "owner@demo.corp",
        name: "owner",
        tenantId: "demo-corp",
        identityId: "isam_id_1",
      },
      accessToken: "access_opaque_token",
      refreshToken: "refresh_opaque_token",
      authMode: "isam",
      accessExpiresAt: null,
      mfaReady: false,
    });
    localStorage.setItem(
      "ewp_session_v1",
      JSON.stringify({
        user: {
          id: "isam_id_1",
          email: "owner@demo.corp",
          name: "owner",
          tenantId: "demo-corp",
          identityId: "isam_id_1",
        },
        accessToken: "access_opaque_token",
        refreshToken: "refresh_opaque_token",
        authMode: "isam",
      }),
    );
  });

  it("does not logout ISAM session when refresh fails", async () => {
    const ok = await useAuthStore.getState().refreshSession();
    expect(ok).toBe(false);
    expect(useAuthStore.getState().user?.email).toBe("owner@demo.corp");
    expect(useAuthStore.getState().accessToken).toBe("access_opaque_token");
    expect(localStorage.getItem("ewp_session_v1")).toBeTruthy();
  });
});
