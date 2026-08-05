import { describe, expect, it } from "vitest";
import {
  isDemoAuthEnabled,
  isLocalDemoToken,
  loginViaDemoAuth,
  mintLocalDemoJwt,
} from "@/auth/demoAuthProvider";
import { isJwtToken, validateSessionOnline } from "@/auth/identityApi";

describe("Sprint 27.1.1 local demo auth", () => {
  it("mints JWT-shaped tokens without legacy .demo suffix", () => {
    const token = mintLocalDemoJwt({ sub: "u1", email: "owner@demo.corp", tid: "demo-corp" });
    expect(token.includes(".demo")).toBe(false);
    expect(isJwtToken(token)).toBe(true);
    expect(isLocalDemoToken(token)).toBe(true);
  });

  it("accepts demo credentials and rejects others", () => {
    const ok = loginViaDemoAuth("owner@demo.corp", "demo", "demo-corp");
    expect(ok.accessToken.split(".")).toHaveLength(3);
    expect(ok.user.roleId).toBe("platform_owner");
    expect(() => loginViaDemoAuth("owner@demo.corp", "wrong", "demo-corp")).toThrow(/rejected/i);
  });

  it("validates local demo session online", async () => {
    const session = loginViaDemoAuth("ops@demo.corp", "demo", "demo-corp");
    await expect(validateSessionOnline(session.accessToken)).resolves.toBe(true);
  });

  it("enables demo auth in test/dev by default", () => {
    expect(isDemoAuthEnabled()).toBe(true);
  });
});
