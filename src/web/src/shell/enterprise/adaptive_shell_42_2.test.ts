/**
 * Sprint 42.2 — Adaptive Enterprise Shell tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  useAdaptiveShellStore,
  ADAPTIVE_SHELL_KEY,
  normalizeLayoutRole,
} from "@/shell/enterprise/adaptiveShellStore";
import { wsKey } from "@/multi-role/workspaceSlot";
import { messages } from "@/i18n/messages";

describe("Sprint 42.2 adaptive enterprise shell", () => {
  beforeEach(() => {
    localStorage.clear();
    useAdaptiveShellStore.setState({
      sidebarCollapsed: false,
      headerCollapsed: false,
      activityMode: "hidden",
      runtimeMode: "compact",
      focusMode: false,
      preFocus: null,
      roleKey: "default",
    });
  });

  it("normalizes layout roles", () => {
    expect(normalizeLayoutRole("owner")).toBe("owner");
    expect(normalizeLayoutRole("administrator")).toBe("administrator");
    expect(normalizeLayoutRole("manager")).toBe("manager");
    expect(normalizeLayoutRole("client")).toBe("client");
    expect(normalizeLayoutRole("sales")).toBe("manager");
  });

  it("persists sidebar and header collapse per role", () => {
    useAdaptiveShellStore.getState().hydrateForRole("owner");
    useAdaptiveShellStore.getState().setSidebarCollapsed(true);
    useAdaptiveShellStore.getState().setHeaderCollapsed(true);
    const raw = localStorage.getItem(wsKey(ADAPTIVE_SHELL_KEY));
    expect(raw).toBeTruthy();
    const vault = JSON.parse(raw!);
    expect(vault.owner.sidebarCollapsed).toBe(true);
    expect(vault.owner.headerCollapsed).toBe(true);

    useAdaptiveShellStore.getState().hydrateForRole("client");
    expect(useAdaptiveShellStore.getState().sidebarCollapsed).toBe(false);
    useAdaptiveShellStore.getState().setSidebarCollapsed(true);
    useAdaptiveShellStore.getState().hydrateForRole("owner");
    expect(useAdaptiveShellStore.getState().sidebarCollapsed).toBe(true);
  });

  it("cycles activity Expanded → Compact → Hidden", () => {
    useAdaptiveShellStore.getState().setActivityMode("expanded");
    useAdaptiveShellStore.getState().cycleActivity();
    expect(useAdaptiveShellStore.getState().activityMode).toBe("compact");
    useAdaptiveShellStore.getState().cycleActivity();
    expect(useAdaptiveShellStore.getState().activityMode).toBe("hidden");
    useAdaptiveShellStore.getState().cycleActivity();
    expect(useAdaptiveShellStore.getState().activityMode).toBe("expanded");
  });

  it("cycles runtime Expanded → Compact → Hidden", () => {
    useAdaptiveShellStore.getState().setRuntimeMode("expanded");
    useAdaptiveShellStore.getState().cycleRuntime();
    expect(useAdaptiveShellStore.getState().runtimeMode).toBe("compact");
    useAdaptiveShellStore.getState().cycleRuntime();
    expect(useAdaptiveShellStore.getState().runtimeMode).toBe("hidden");
  });

  it("focus mode hides chrome and restores previous layout", () => {
    useAdaptiveShellStore.getState().setSidebarCollapsed(false);
    useAdaptiveShellStore.getState().setHeaderCollapsed(false);
    useAdaptiveShellStore.getState().setActivityMode("expanded");
    useAdaptiveShellStore.getState().setRuntimeMode("expanded");
    useAdaptiveShellStore.getState().setFocusMode(true);
    expect(useAdaptiveShellStore.getState().focusMode).toBe(true);
    expect(useAdaptiveShellStore.getState().sidebarCollapsed).toBe(true);
    expect(useAdaptiveShellStore.getState().headerCollapsed).toBe(true);
    expect(useAdaptiveShellStore.getState().activityMode).toBe("hidden");
    expect(useAdaptiveShellStore.getState().runtimeMode).toBe("hidden");
    useAdaptiveShellStore.getState().setFocusMode(false);
    expect(useAdaptiveShellStore.getState().focusMode).toBe(false);
    expect(useAdaptiveShellStore.getState().activityMode).toBe("expanded");
    expect(useAdaptiveShellStore.getState().runtimeMode).toBe("expanded");
  });

  it("has RU shell keys", () => {
    for (const k of [
      "shell.focus.toggle",
      "shell.sidebar.collapse",
      "shell.activity.cycle",
      "shell.runtime.hide",
    ]) {
      expect(messages.ru[k], k).toBeTruthy();
    }
  });
});
