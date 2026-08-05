import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PlatformPulsePanel } from "./PlatformPulsePanel";
import { DashboardWorkspaceWidgets } from "@/workspace-engine/DashboardWorkspaceWidgets";
import { useWorkspaceRouteSync } from "@/workspace-engine/useWorkspaceTabs";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { WORKSPACE_SESSION_KEY } from "@/workspace-engine/types";

function WorkspaceSyncHarness({ label }: { label: string }) {
  useWorkspaceRouteSync();
  return <div aria-label={label}>workspace-ready</div>;
}

/**
 * Guards against Zustand selectors that return a new array each call
 * (Maximum update depth exceeded).
 */
describe("Sprint 27.3 render-loop smoke", () => {
  it("PlatformPulsePanel settles without infinite updates", async () => {
    render(
      <MemoryRouter>
        <PlatformPulsePanel />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByLabelText("Platform pulse")).toBeInTheDocument();
    });
    // Second paint must not throw Maximum update depth exceeded
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.getByLabelText("Platform pulse")).toBeInTheDocument();
  });

  it("DashboardWorkspaceWidgets settles without infinite updates", async () => {
    const { container } = render(
      <MemoryRouter>
        <DashboardWorkspaceWidgets />
      </MemoryRouter>,
    );
    await new Promise((r) => setTimeout(r, 50));
    expect(container.textContent?.length).toBeGreaterThan(0);
  });

  it("workspace route sync is idempotent on remount/path", async () => {
    localStorage.removeItem(WORKSPACE_SESSION_KEY);
    useWorkspaceManager.setState({
      activeWorkspaceId: "ws_default",
      tabs: [],
      activeTabId: null,
      hydrated: false,
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<WorkspaceSyncHarness label="dash-sync" />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("dash-sync")).toBeInTheDocument();
      expect(useWorkspaceManager.getState().hydrated).toBe(true);
    });
    await new Promise((r) => setTimeout(r, 80));
    const before = useWorkspaceManager.getState().tabs.length;
    useWorkspaceManager.getState().syncRoute("/dashboard");
    useWorkspaceManager.getState().syncRoute("/dashboard");
    expect(useWorkspaceManager.getState().tabs.length).toBe(before);
  });
});
