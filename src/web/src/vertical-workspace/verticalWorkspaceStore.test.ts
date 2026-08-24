/**
 * Sprint 46.6 — stale localStorage migration for the vertical workspace store.
 *
 * Keys must be written/read through wsKey() (not the raw literal) — jsdom's
 * default test origin is http://localhost:3000, which WORKSPACE_PORT_SLOTS
 * maps to the "owner" slot, so the store actually reads/writes a prefixed
 * key (ews_ws_owner__ewp_vertical_workspace_v1) in this test environment.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { wsKey } from "@/multi-role/workspaceSlot";

describe("verticalWorkspaceStore migration (Sprint 46.6)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
  });

  it("migrates a still-valid v1 value to v2 and drops the legacy key", async () => {
    localStorage.setItem(wsKey("ewp_vertical_workspace_v1"), "auto");
    const { useVerticalWorkspaceStore } = await import("./verticalWorkspaceStore");
    expect(useVerticalWorkspaceStore.getState().verticalId).toBe("auto");
    expect(localStorage.getItem(wsKey("ewp_vertical_workspace_v2"))).toBe("auto");
    expect(localStorage.getItem(wsKey("ewp_vertical_workspace_v1"))).toBeNull();
  });

  it("resets to owner (not a stale/misleading vertical) when the persisted id no longer resolves", async () => {
    localStorage.setItem(wsKey("ewp_vertical_workspace_v1"), "some_removed_vertical_id");
    const { useVerticalWorkspaceStore } = await import("./verticalWorkspaceStore");
    expect(useVerticalWorkspaceStore.getState().verticalId).toBe("owner");
  });

  it("prefers the v2 value over a stale v1 value when both are present", async () => {
    localStorage.setItem(wsKey("ewp_vertical_workspace_v2"), "beauty");
    localStorage.setItem(wsKey("ewp_vertical_workspace_v1"), "auto");
    const { useVerticalWorkspaceStore } = await import("./verticalWorkspaceStore");
    expect(useVerticalWorkspaceStore.getState().verticalId).toBe("beauty");
  });

  it("setVerticalId refuses to persist an unknown vertical id", async () => {
    const { useVerticalWorkspaceStore } = await import("./verticalWorkspaceStore");
    useVerticalWorkspaceStore.getState().setVerticalId("not_a_real_vertical");
    expect(useVerticalWorkspaceStore.getState().verticalId).not.toBe("not_a_real_vertical");
  });
});
