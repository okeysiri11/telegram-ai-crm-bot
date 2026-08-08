/**
 * Sprint 41.1 — GlobeFly demo package smoke tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  GLOBEFLY_DEMO_USERS,
  GLOBEFLY_SEED,
  GLOBEFLY_TENANT_ID,
  applyGlobeFlySession,
  isGlobeFlyEmail,
  persistGlobeFlySeed,
  readGlobeFlySeed,
} from "@/demo/globefly";
import { loginViaDemoAuth } from "@/auth/demoAuthProvider";
import { useViewModeStore, VIEW_MODE_KEY } from "@/ux-revolution";
import { useOrgSelector } from "@/navigation/orgSelectorStore";

describe("Sprint 41.1 GlobeFly demo", () => {
  beforeEach(() => {
    localStorage.clear();
    useViewModeStore.setState({ viewMode: "platform_owner" });
  });

  it("defines GlobeFly users including Client", () => {
    expect(GLOBEFLY_TENANT_ID).toBe("globefly");
    expect(GLOBEFLY_DEMO_USERS.some((u) => u.email === "client@globefly.demo")).toBe(true);
    expect(isGlobeFlyEmail("client@globefly.demo")).toBe(true);
    expect(GLOBEFLY_SEED.clients.length).toBeGreaterThan(0);
    expect(GLOBEFLY_SEED.deals.length).toBeGreaterThan(0);
  });

  it("demo auth accepts GlobeFly client", () => {
    const session = loginViaDemoAuth("client@globefly.demo", "demo", "globefly");
    expect(session.user.tenantId).toBe("globefly");
    expect(session.user.roleId).toBe("client");
    expect(session.accessToken).toBeTruthy();
  });

  it("applyGlobeFlySession sets Client view mode and org", () => {
    applyGlobeFlySession("client@globefly.demo");
    expect(useViewModeStore.getState().viewMode).toBe("client");
    expect(useOrgSelector.getState().organizationId).toBe("globefly");
    expect(localStorage.getItem(VIEW_MODE_KEY)).toBe("client");
    persistGlobeFlySeed();
    expect(readGlobeFlySeed()?.company.name).toBe("GlobeFly");
  });
});
