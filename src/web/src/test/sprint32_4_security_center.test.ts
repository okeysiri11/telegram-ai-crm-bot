import { describe, expect, it } from "vitest";
import { securityCenter } from "../../auth/managers/securityCenter";
import { webConfig } from "../config/webConfig";

describe("Sprint 32.4 Enterprise Security Center", () => {
  it("exposes zero trust snapshot fields", () => {
    const snap = securityCenter.snapshot();
    expect(snap.zeroTrust).toBe(true);
    expect(snap.version).toBe("32.4");
    expect(snap.health).toBe("healthy");
    expect(securityCenter.capabilities().systemOfRecord).toContain("security_center");
    expect(webConfig.sprint).toBe("33.2");
  });
});
