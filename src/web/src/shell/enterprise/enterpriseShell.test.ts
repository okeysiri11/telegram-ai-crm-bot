import { describe, expect, it, beforeEach } from "vitest";
import { ENTERPRISE_SHELL_NAV } from "@/shell/enterprise/enterpriseNav";
import { ENTERPRISE_MODULE_CARDS } from "@/dashboard/enterpriseModuleCards";
import { STATUS_PROBES } from "@/shell/enterprise/statusCatalog";
import { ACTIVITY_TABS } from "@/shell/enterprise/activityCatalog";
import {
  shellModuleRegistry,
  SHELL_MODULE_REGISTRY_VERSION,
} from "@/shell/enterprise/shellModuleRegistry";
import { enterpriseShellRuntime } from "@/shell/enterprise/enterpriseShellRuntime";
import { SHELL_QUICK_ACTIONS } from "@/shell/enterprise/shellQuickActions";
import { refreshShellSearch } from "@/shell/enterprise/shellSearch";
import { buildActivityTimeline } from "@/shell/enterprise/activityTimeline";
import { useShellPreferences } from "@/shell/enterprise/shellPreferencesStore";
import { searchIndex } from "../../../navigation/managers/searchIndex";

describe("Sprint 27.1 enterprise shell catalogs", () => {
  it("exposes required sidebar sections", () => {
    const labels = ENTERPRISE_SHELL_NAV.map((n) => n.label);
    for (const required of [
      "Панель управления",
      "CRM",
      "ERP",
      "Проекты",
      "Студия AI",
      "AI-агенты",
      "База знаний",
      "Документы",
      "Аналитика",
      "Маркетплейс",
      "Автоматизация",
      "Интеграции",
      "Безопасность",
      "Корпоративный город",
      "Настройки",
    ]) {
      expect(labels).toContain(required);
    }
    expect(ENTERPRISE_SHELL_NAV.every((n) => Boolean(n.icon))).toBe(true);
    expect(ENTERPRISE_SHELL_NAV.map((n) => n.route)).toEqual(
      expect.arrayContaining(["/crm", "/erp", "/ai-studio", "/ai-agents", "/enterprise-city", "/settings"]),
    );
  });

  it("exposes dashboard module cards with stats", () => {
    expect(ENTERPRISE_MODULE_CARDS).toHaveLength(10);
    for (const card of ENTERPRISE_MODULE_CARDS) {
      expect(card.stats.length).toBeGreaterThan(0);
      expect(card.route.startsWith("/")).toBe(true);
    }
  });

  it("exposes status bar and activity tabs", () => {
    expect(STATUS_PROBES.map((p) => p.id)).toEqual([
      "runtime",
      "api",
      "database",
      "providers",
      "voice",
      "mcp",
      "queue",
      "build",
      "version",
    ]);
    expect(ACTIVITY_TABS).toHaveLength(5);
  });
});

describe("Sprint 28.5 Enterprise Shell runtime", () => {
  beforeEach(() => {
    useShellPreferences.setState({
      hydrated: false,
      favorites: [],
      pinned: ["dashboard", "desktop", "ai_studio", "city"],
      recentModuleIds: [],
      collapsedCategories: [],
      sidebarCollapsed: false,
    });
  });

  it("registers required platform modules including Desktop and Production", () => {
    expect(SHELL_MODULE_REGISTRY_VERSION).toBe("28.5");
    const ids = shellModuleRegistry.list().map((m) => m.id);
    for (const required of [
      "dashboard",
      "desktop",
      "city",
      "crm",
      "erp",
      "ai_studio",
      "production_studio",
      "knowledge",
      "marketplace",
      "automation",
      "analytics",
      "settings",
    ]) {
      expect(ids).toContain(required);
    }
    const nav = shellModuleRegistry.toNavItems();
    expect(nav.find((n) => n.id === "desktop")?.route).toBe("/desktop");
    expect(nav.find((n) => n.id === "production_studio")?.label).toBe("Продакшн");
  });

  it("supports dynamic module registration and unload", () => {
    shellModuleRegistry.register({
      id: "dyn_test",
      label: "Dynamic Test",
      route: "/dyn-test",
      icon: "dashboard",
      category: "system",
      keywords: ["dynamic"],
      source: "dynamic",
    });
    expect(shellModuleRegistry.get("dyn_test")?.label).toBe("Dynamic Test");
    expect(enterpriseShellRuntime.unloadModule("dyn_test")).toBe(true);
    expect(shellModuleRegistry.get("dyn_test")).toBeUndefined();
  });

  it("boots shell lifecycle and indexes search + quick actions", async () => {
    const snap = await enterpriseShellRuntime.startup();
    expect(["ready", "starting", "restoring"]).toContain(snap.phase);
    expect(snap.modules).toBeGreaterThanOrEqual(12);
    expect(SHELL_QUICK_ACTIONS.length).toBeGreaterThanOrEqual(8);
    refreshShellSearch();
    const docs = searchIndex.list();
    expect(docs.some((d) => d.id.startsWith("shell_mod_"))).toBe(true);
    expect(docs.some((d) => d.id.startsWith("shell_qa_") || d.title.includes("Open Studio"))).toBe(true);
  });

  it("persists favorites pins and recents", () => {
    useShellPreferences.getState().hydrate();
    useShellPreferences.getState().toggleFavorite("crm");
    useShellPreferences.getState().togglePin("erp");
    useShellPreferences.getState().rememberModule("ai_studio");
    const s = useShellPreferences.getState();
    expect(s.favorites).toContain("crm");
    expect(s.pinned).toContain("erp");
    expect(s.recentModuleIds[0]).toBe("ai_studio");
  });

  it("builds unified activity timeline", () => {
    const items = buildActivityTimeline(10);
    expect(Array.isArray(items)).toBe(true);
  });
});
