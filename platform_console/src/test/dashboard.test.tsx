import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "../pages/DashboardPage";
import { KernelPage } from "../pages/KernelPage";
import { RuntimeContext } from "../context/RuntimeContext";
import type { useLiveRuntime } from "../hooks/useLiveRuntime";

function mockLive(
  overrides: Partial<ReturnType<typeof useLiveRuntime>> = {},
): ReturnType<typeof useLiveRuntime> {
  const q = <T,>(data: T) =>
    ({
      data,
      isSuccess: true,
      isLoading: false,
      error: null,
    }) as never;

  return {
    socket: { status: "open", lastMessage: null, events: [] },
    health: q({ status: "ok" }),
    status: q({
      version: "1.1.0",
      kernel: "OK",
      eventBus: "OK",
      serviceMesh: "OK",
      workflowEngine: "OK",
      runtimeServer: "OK",
      services: 3,
      systemStatus: "READY",
    }),
    metrics: q({
      uptimeSec: 42,
      memory: { rss: 1e7, heapUsed: 5e6, heapTotal: 1e7, external: 1e5 },
      cpu: { userMicros: 1000, systemMicros: 500 },
      startedAt: "2026-01-01T00:00:00.000Z",
    }),
    kernel: q({
      version: "1.4.0",
      platformVersion: "1.1.0",
      state: "Started",
      startedAt: "2026-01-01T00:00:00.000Z",
      uptimeMs: 42000,
      modules: ["ados.event_bus"],
      services: 1,
      health: "healthy",
    }),
    services: q([]),
    workflows: q({ workflows: [], instances: [] }),
    events: q([]),
    logs: q([]),
    agents: q([]),
    connected: true,
    ...overrides,
  };
}

function wrap(ui: React.ReactNode, live = mockLive()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <RuntimeContext.Provider value={live}>
        <MemoryRouter>{ui}</MemoryRouter>
      </RuntimeContext.Provider>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders live status cards from Runtime context", () => {
    wrap(<DashboardPage />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getAllByText("READY").length).toBeGreaterThan(0);
    expect(screen.getByText("Event Bus")).toBeInTheDocument();
    expect(screen.getByText("Service Mesh")).toBeInTheDocument();
    expect(screen.getByText("Workflow Engine")).toBeInTheDocument();
  });
});

describe("Kernel page", () => {
  it("shows kernel fields from live Runtime data", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <RuntimeContext.Provider value={mockLive()}>
          <MemoryRouter initialEntries={["/kernel"]}>
            <Routes>
              <Route path="/kernel" element={<KernelPage />} />
            </Routes>
          </MemoryRouter>
        </RuntimeContext.Provider>
      </QueryClientProvider>,
    );
    expect(screen.getByText("Kernel Version")).toBeInTheDocument();
    expect(screen.getByText("1.4.0")).toBeInTheDocument();
  });
});
