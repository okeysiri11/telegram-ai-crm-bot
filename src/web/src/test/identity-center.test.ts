import { describe, expect, it } from "vitest";
import {
  AUTH_UI_VERSION,
  buildAuthenticationDashboard,
  loginSchema,
  mfaCenter,
  organizationManager,
  permissionManager,
  roleManager,
  sessionManager,
  userManager,
} from "../../auth";

describe("Enterprise Identity Center", () => {
  it("exposes version and auth schemas", () => {
    expect(AUTH_UI_VERSION).toBe("9.0.5");
    expect(loginSchema.safeParse({
      identifier: "owner@demo.corp",
      password: "demo",
      rememberMe: true,
      tenantId: "demo-corp",
      language: "en",
    }).success).toBe(true);
  });

  it("covers managers and MFA", () => {
    expect(userManager.list().length).toBeGreaterThan(0);
    expect(organizationManager.list().some((o) => o.kind === "company")).toBe(true);
    expect(roleManager.list().length).toBeGreaterThanOrEqual(4);
    expect(permissionManager.syncWithCoreRbac().synced).toBe(true);
    expect(mfaCenter.methods).toContain("totp");
    expect(mfaCenter.extensionsReady).toContain("webauthn");
    expect(sessionManager.activeSessions().length).toBeGreaterThan(0);
  });

  it("builds authentication dashboard", () => {
    const dash = buildAuthenticationDashboard();
    expect(dash.userOverview.total).toBeGreaterThan(0);
    expect(dash.mfaAdoption.methods.length).toBeGreaterThan(0);
    expect(dash.permissions).toContain("crm");
  });
});
