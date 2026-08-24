/**
 * Sprint 46.6 — onboarding → authenticated workspace transition stabilization.
 *
 * Root cause of the "Maximum update depth exceeded" crash reported after
 * registration/onboarding: UnifiedIntentBar (rendered unconditionally by
 * TopNavigation, which FullLayout renders on every authenticated route) and
 * TaskInboxPanel selected Zustand store state via `s.recent(5)` /
 * `s.byFilter(filter)` — both call Array.prototype.slice/filter, which
 * return a brand-new array reference on every call. Used directly as a
 * useSyncExternalStore selector, a new reference on every snapshot check
 * makes React believe the store changed on every render, scheduling another
 * render forever. This is not vertical-specific — it reproduced on every
 * FullLayout-wrapped route (/dashboard, /vertical/owner, /vertical/auto,
 * /vertical/beauty, ...), which is why it surfaced right after onboarding
 * hands off into the authenticated shell. Fixed in UnifiedIntentBar.tsx and
 * TaskInboxPanel.tsx by selecting the stable `items` array and deriving the
 * slice/filter with useMemo instead.
 */

import { describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { CommandCenterProvider } from "../../command-center/components/CommandCenterProvider";
import { NavigationProvider } from "../../navigation/components/NavigationProvider";
import { FullLayout } from "@/layouts/FullLayout";
import { VerticalWorkspacePage } from "./VerticalWorkspacePage";
import { useVerticalWorkspaceStore } from "./verticalWorkspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { useViewModeStore } from "@/ux-revolution/viewModeStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { wsKey } from "@/multi-role/workspaceSlot";

function Shell({ initial }: { initial: string }) {
  return (
    <MemoryRouter initialEntries={[initial]}>
      <CommandCenterProvider>
        <NavigationProvider>
          <Routes>
            <Route
              path="/vertical/:verticalId"
              element={
                <FullLayout>
                  <VerticalWorkspacePage />
                </FullLayout>
              }
            />
          </Routes>
        </NavigationProvider>
      </CommandCenterProvider>
    </MemoryRouter>
  );
}

async function renderAndCheckNoLoop(initial: string) {
  const err = vi.spyOn(console, "error").mockImplementation(() => {});
  const utils = render(<Shell initial={initial} />);
  await waitFor(() => {
    expect(screen.getByTestId("vertical-workspace-shell")).toBeInTheDocument();
  });
  await act(async () => {
    await new Promise((r) => setTimeout(r, 100));
  });
  const depth = err.mock.calls.some((c) =>
    String(c[0] ?? "").includes("Maximum update depth exceeded"),
  );
  err.mockRestore();
  expect(depth).toBe(false);
  return utils;
}

describe("Sprint 46.6 — post-onboarding authenticated workspace transition", () => {
  it("clean registration → authenticated workspace renders without an infinite update loop, with correct vertical state", async () => {
    useVerticalWorkspaceStore.getState().setVerticalId("owner");
    await renderAndCheckNoLoop("/vertical/owner");
    expect(screen.getByTestId("vertical-workspace-shell")).toHaveAttribute(
      "data-vertical",
      "owner",
    );
    expect(useVerticalWorkspaceStore.getState().verticalId).toBe("owner");
  });

  it("page refresh after registration preserves the active vertical via persisted storage", async () => {
    useVerticalWorkspaceStore.getState().setVerticalId("auto");
    expect(localStorage.getItem(wsKey("ewp_vertical_workspace_v2"))).toBe("auto");

    const { unmount } = await renderAndCheckNoLoop("/vertical/auto");
    unmount();

    // Simulate a hard refresh: reset the in-memory store and re-derive from
    // the persisted key only (loadId() re-runs on module init in the app).
    vi.resetModules();
    const { useVerticalWorkspaceStore: reloaded } = await import("./verticalWorkspaceStore");
    expect(reloaded.getState().verticalId).toBe("auto");
  });

  it("Beauty → Auto → Agro switching settles without a render loop and without state bleed", async () => {
    for (const id of ["beauty", "auto", "agro"]) {
      const { unmount } = await renderAndCheckNoLoop(`/vertical/${id}`);
      expect(screen.getByTestId("vertical-workspace-shell")).toHaveAttribute("data-vertical", id);
      expect(useVerticalWorkspaceStore.getState().verticalId).toBe(id);
      unmount();
    }
  });

  it("stale localStorage migration does not loop and resets to a safe default", async () => {
    localStorage.clear();
    localStorage.setItem(wsKey("ewp_vertical_workspace_v1"), "some_removed_vertical_id");
    vi.resetModules();
    const { useVerticalWorkspaceStore: reloaded } = await import("./verticalWorkspaceStore");
    expect(reloaded.getState().verticalId).toBe("owner");
    reloaded.getState().setVerticalId("owner");
    await renderAndCheckNoLoop("/vertical/owner");
  });

  it("view-as (view mode / role switcher / workspace) never mutates the authenticated user session", async () => {
    useAuthStore.setState({
      user: {
        id: "u-46-6",
        email: "owner@ados.demo",
        name: "ADOS Owner",
        tenantId: "ados",
        roleId: "platform_owner",
        permissions: ["read", "write", "admin"],
      },
      accessToken: "access_test_46_6",
      refreshToken: "refresh_test_46_6",
      authMode: "isam",
    });

    useViewModeStore.getState().setViewMode("client");
    useRoleSwitcher.getState().setRole("client");
    useVerticalWorkspaceStore.getState().setVerticalId("beauty");

    expect(useAuthStore.getState().user?.email).toBe("owner@ados.demo");
    expect(useAuthStore.getState().user?.roleId).toBe("platform_owner");
    expect(useAuthStore.getState().user?.permissions).toEqual(["read", "write", "admin"]);
    expect(useAuthStore.getState().accessToken).toBe("access_test_46_6");

    useViewModeStore.getState().setViewMode("platform_owner");
    useRoleSwitcher.getState().setRole("owner");
  });
});
