/**
 * Sprint 33.2 — Intelligent Navigation accordion tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  groupsForMode,
  resolveGroupForPath,
  isNavItemActive,
  INTELLIGENT_NAV_GROUPS,
  NAV_ACCORDION_KEY,
  useNavAccordionStore,
  UX_REVOLUTION_SPRINT,
} from "@/ux-revolution";
import { webConfig } from "@/config/webConfig";

describe("Sprint 33.2 Intelligent Navigation", () => {
  beforeEach(() => {
    localStorage.removeItem(NAV_ACCORDION_KEY);
    useNavAccordionStore.setState({ expandedId: "workspace" });
  });

  it("bumps sprint to 33.2", () => {
    expect(webConfig.sprint).toBe("33.2");
    expect(UX_REVOLUTION_SPRINT).toBe("33.2");
  });

  it("defines six canonical groups", () => {
    expect(INTELLIGENT_NAV_GROUPS.map((g) => g.id)).toEqual([
      "workspace",
      "business",
      "ai",
      "city",
      "platform",
      "owner",
    ]);
  });

  it("Simple Mode shows only Workspace, Business, AI", () => {
    const ids = groupsForMode("simple").map((g) => g.id);
    expect(ids).toEqual(["workspace", "business", "ai"]);
    expect(groupsForMode("simple").every((g) => g.items.every((i) => i.simple))).toBe(true);
  });

  it("Pro Mode shows all non-owner groups", () => {
    const ids = groupsForMode("pro").map((g) => g.id);
    expect(ids).toEqual(["workspace", "business", "ai", "city", "platform"]);
    expect(ids).not.toContain("owner");
  });

  it("Owner Mode shows every group including Owner", () => {
    const ids = groupsForMode("simple", { owner: true }).map((g) => g.id);
    expect(ids).toEqual(["workspace", "business", "ai", "city", "platform", "owner"]);
  });

  it("accordion expands one group at a time and persists", () => {
    const store = useNavAccordionStore.getState();
    store.expand("business");
    expect(useNavAccordionStore.getState().expandedId).toBe("business");
    expect(localStorage.getItem(NAV_ACCORDION_KEY)).toBe("business");
    store.toggle("ai");
    expect(useNavAccordionStore.getState().expandedId).toBe("ai");
    store.toggle("ai");
    expect(useNavAccordionStore.getState().expandedId).toBeNull();
  });

  it("resolves group and active item for CRM path", () => {
    expect(resolveGroupForPath("/crm")).toBe("business");
    expect(resolveGroupForPath("/ai-agents")).toBe("ai");
    expect(resolveGroupForPath("/city")).toBe("city");
    const crm = INTELLIGENT_NAV_GROUPS.find((g) => g.id === "business")!.items.find((i) => i.id === "biz_crm")!;
    expect(isNavItemActive(crm, "/crm", "")).toBe(true);
  });
});
