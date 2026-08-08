/**
 * Sprint 42.6 — duplicate top navigation strip gated for Developer opt-in only.
 */

import { describe, expect, it, beforeEach } from "vitest";
import {
  shouldShowWorkspaceTabBar,
  useWorkspaceTabChromeStore,
} from "@/workspace-engine/workspaceTabChromeStore";

describe("Sprint 42.6 remove duplicate top navigation", () => {
  beforeEach(() => {
    useWorkspaceTabChromeStore.setState({ enabled: false });
  });

  it("hides tab strip for Owner, Admin, Manager, Client even if preference is on", () => {
    for (const mode of ["platform_owner", "company_admin", "manager", "client"] as const) {
      expect(shouldShowWorkspaceTabBar(mode, true)).toBe(false);
      expect(shouldShowWorkspaceTabBar(mode, false)).toBe(false);
    }
  });

  it("shows tab strip for Developer only when manually enabled", () => {
    expect(shouldShowWorkspaceTabBar("developer", false)).toBe(false);
    expect(shouldShowWorkspaceTabBar("developer", true)).toBe(true);
  });

  it("defaults store preference to off", () => {
    expect(useWorkspaceTabChromeStore.getState().enabled).toBe(false);
  });

  it("toggle updates preference", () => {
    useWorkspaceTabChromeStore.getState().setEnabled(true);
    expect(useWorkspaceTabChromeStore.getState().enabled).toBe(true);
    useWorkspaceTabChromeStore.getState().setEnabled(false);
    expect(useWorkspaceTabChromeStore.getState().enabled).toBe(false);
  });
});
