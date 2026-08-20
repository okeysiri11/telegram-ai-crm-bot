import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DEBUG_NOTIFICATION_FIXTURES, useNotificationStore } from "@/notifications/notificationStore";
import {
  navFromVertical,
  PLATFORM_MANAGEMENT_NAV,
  verticalIdFromPath,
  workspaceHomePath,
  workspaceLabel,
  isDemoAccount,
  sectionTitle,
} from "@/shell/mobile";
import { MobileHome } from "@/shell/mobile/MobileHome";
import { UnifiedToastStrip } from "@/workspace-chrome/UnifiedToastStrip";

describe("mobile workspace navigation", () => {
  it("resolves verticals from path without hardcoding agro", () => {
    expect(verticalIdFromPath("/workspace/auto")).toBe("auto");
    expect(verticalIdFromPath("/vertical/agro/deals")).toBe("agro");
    expect(verticalIdFromPath("/workspace/crypto")).toBe("crypto");
    expect(verticalIdFromPath("/workspace/legal")).toBe("legal");
    expect(workspaceLabel("agro")).toBe("Агро");
    expect(workspaceHomePath("auto")).toContain("/workspace/auto");
  });

  it("builds nav from each vertical catalog", () => {
    for (const id of ["agro", "auto", "crypto", "legal", "beauty", "cafe", "drone", "crm"]) {
      const items = navFromVertical(id);
      expect(items.length).toBeGreaterThan(3);
      expect(items.some((item) => item.label.length > 0)).toBe(true);
    }
  });

  it("keeps platform management off the home path list", () => {
    expect(PLATFORM_MANAGEMENT_NAV.some((i) => i.label.includes("System Health") || i.href === "/health")).toBe(
      true,
    );
  });

  it("marks demo accounts without treating them as production", () => {
    expect(isDemoAccount("owner@demo.corp", "demo-corp")).toBe(true);
    expect(isDemoAccount("ops@company.io", "org-prod")).toBe(false);
  });

  it("reads section titles from view query", () => {
    expect(sectionTitle("/workspace/agro", "?view=deals", "agro", navFromVertical("agro"))).toBe("Сделки");
  });
});

describe("notification seed policy", () => {
  it("does not auto-load demo toast fixtures", () => {
    expect(DEBUG_NOTIFICATION_FIXTURES.some((n) => n.title === "AI insight ready")).toBe(true);
    expect(useNotificationStore.getState().items.some((n) => n.title === "AI insight ready")).toBe(false);
  });

  it("does not toast historical unread items on mount", () => {
    useNotificationStore.setState({
      items: [
        {
          id: "hist",
          kind: "ai",
          title: "AI insight ready",
          body: "Weekly forecast available",
          createdAt: new Date().toISOString(),
          read: false,
        },
      ],
    });
    render(<UnifiedToastStrip />);
    expect(screen.queryByText("AI insight ready")).toBeNull();
  });
});

describe("mobile home", () => {
  it("shows workspace, quick actions, and collapsed analytics", () => {
    render(
      <MemoryRouter>
        <MobileHome workspaceId="agro" workspaceLabel="Агро" roleLabel="Директор" />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-home-workspace")).toHaveTextContent("Агро");
    expect(screen.getByText("Открыть рабочее пространство")).toBeInTheDocument();
    expect(screen.getByText("Быстрые действия")).toBeInTheDocument();
    expect(screen.getByText("Показать аналитику")).toBeInTheDocument();
    expect(screen.queryByText("NPS")).toBeNull();
  });
});
