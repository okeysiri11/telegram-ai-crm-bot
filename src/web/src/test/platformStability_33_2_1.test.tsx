/**
 * Sprint 33.2.1 — Platform Stability smoke.
 * Guards against Maximum update depth exceeded on shared surfaces + route walk.
 */

import { describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { webConfig } from "@/config/webConfig";
import { useSharedContext, useIntegrationBoot } from "@/integration-hub";
import { useIntegrationContext } from "@/integration-hub/integrationContextStore";
import { ExecutiveSummaryDashboard } from "@/ux-revolution/ExecutiveSummaryDashboard";
import { useExperienceModeStore } from "@/ux-revolution/experienceModeStore";
import { useNavAccordionStore } from "@/ux-revolution/navAccordionStore";
import { CommandCenterProvider } from "../../command-center/components/CommandCenterProvider";
import { NavigationProvider } from "../../navigation/components/NavigationProvider";

const PLATFORM_ROUTES = [
  "/dashboard",
  "/workspace",
  "/enterprise-city",
  "/crm",
  "/erp",
  "/ai-agents",
  "/ai-studio",
  "/production-studio",
  "/projects",
  "/documents",
  "/knowledge",
  "/analytics",
  "/marketplace",
  "/calendar",
  "/notifications",
  "/settings",
  "/owner",
  "/identity/security",
] as const;

function SharedContextProbe() {
  useIntegrationBoot();
  const ctx = useSharedContext();
  return (
    <div data-testid="shared-ctx">
      {ctx.path}|{ctx.moduleId}|{ctx.surface}
    </div>
  );
}

function Shell({ initial }: { initial: string }) {
  return (
    <MemoryRouter initialEntries={[initial]}>
      <CommandCenterProvider>
        <NavigationProvider>
          <Routes>
            <Route path="*" element={<SharedContextProbe />} />
          </Routes>
        </NavigationProvider>
      </CommandCenterProvider>
    </MemoryRouter>
  );
}

describe("Sprint 33.2.1 platform stability", () => {
  it("bumps web sprint to 33.2.1", () => {
    expect(webConfig.sprint).toBe("33.2.1");
  });

  it("useSharedContext settles without update-depth loop", async () => {
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<Shell initial="/dashboard" />);
    await waitFor(() => {
      expect(screen.getByTestId("shared-ctx").textContent).toContain("/dashboard");
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 80));
    });
    expect(screen.getByTestId("shared-ctx")).toBeInTheDocument();
    const depth = err.mock.calls.some((c) =>
      String(c[0] ?? "").includes("Maximum update depth exceeded"),
    );
    err.mockRestore();
    expect(depth).toBe(false);
  });

  it("syncFromRoute is idempotent (no store churn)", () => {
    const a = useIntegrationContext.getState().syncFromRoute("/crm");
    const syncedAt = useIntegrationContext.getState().syncedAt;
    const b = useIntegrationContext.getState().syncFromRoute("/crm");
    expect(a.path).toBe(b.path);
    expect(useIntegrationContext.getState().syncedAt).toBe(syncedAt);
  });

  it("mode / accordion stores skip no-op writes", () => {
    const mode = useExperienceModeStore.getState().mode;
    useExperienceModeStore.getState().setMode(mode);
    expect(useExperienceModeStore.getState().mode).toBe(mode);

    const gid = useNavAccordionStore.getState().expandedId;
    useNavAccordionStore.getState().expand(gid);
    expect(useNavAccordionStore.getState().expandedId).toBe(gid);
  });

  it("Executive Summary (Simple dashboard) settles without update-depth loop", async () => {
    useExperienceModeStore.getState().setMode("simple");
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <MemoryRouter>
        <CommandCenterProvider>
          <NavigationProvider>
            <ExecutiveSummaryDashboard />
          </NavigationProvider>
        </CommandCenterProvider>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Executive Summary/i)).toBeInTheDocument();
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 80));
    });
    const depth = err.mock.calls.some((c) =>
      String(c[0] ?? "").includes("Maximum update depth exceeded"),
    );
    err.mockRestore();
    expect(depth).toBe(false);
  });

  it("route walkthrough: sync every platform path without recursive set", () => {
    let writes = 0;
    const unsub = useIntegrationContext.subscribe(() => {
      writes += 1;
    });
    for (const path of PLATFORM_ROUTES) {
      useIntegrationContext.getState().syncFromRoute(path);
      useIntegrationContext.getState().syncFromRoute(path);
    }
    unsub();
    // One write per distinct path (second sync is no-op)
    expect(writes).toBe(PLATFORM_ROUTES.length);
  });
});
