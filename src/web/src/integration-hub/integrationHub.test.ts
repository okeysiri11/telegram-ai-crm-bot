import { beforeEach, describe, expect, it } from "vitest";
import {
  OS_DEEP_LINKS,
  buildDeepLink,
  parseDeepLink,
  surfaceFromPath,
  enterpriseEventBus,
  sessionCoordinator,
  registerIntegrationSearch,
  useIntegrationContext,
  INTEGRATION_HUB_VERSION,
} from "./index";
import { searchProvider } from "../../navigation/managers/searchProvider";

describe("Sprint 28.0 Integration Hub", () => {
  beforeEach(() => {
    useIntegrationContext.setState({
      workspaceId: "ws_default",
      userId: null,
      userName: null,
      organization: "demo-corp",
      project: "default",
      moduleId: "dashboard",
      surface: "dashboard",
      aiSessionId: null,
      runtimeLabel: "enterprise-web",
      profileId: "ceo",
      path: "/dashboard",
      syncedAt: null,
    });
  });

  it("exposes OS deep links for all required surfaces", () => {
    const surfaces = OS_DEEP_LINKS.map((d) => d.surface);
    expect(surfaces).toEqual(
      expect.arrayContaining([
        "desktop",
        "dashboard",
        "workspace",
        "city",
        "production",
        "command_center",
        "crm",
        "settings",
        "devtools",
      ]),
    );
    expect(INTEGRATION_HUB_VERSION).toBe("28.0");
  });

  it("parses and builds deep links", () => {
    expect(surfaceFromPath("/production-studio")).toBe("production");
    expect(surfaceFromPath("/enterprise-city")).toBe("city");
    expect(surfaceFromPath("/desktop")).toBe("desktop");
    const link = buildDeepLink({ path: "/production-studio", studio: "reels", embed: true });
    expect(link).toContain("studio=reels");
    expect(link).toContain("embed=1");
    const parsed = parseDeepLink("/enterprise-city?building=crm&embed=1");
    expect(parsed.building).toBe("crm");
    expect(parsed.embed).toBe(true);
  });

  it("publishes enterprise events and keeps recent buffer", () => {
    let seen = 0;
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "open_module") seen += 1;
    });
    enterpriseEventBus.openModule("/crm", "desktop");
    enterpriseEventBus.openCityBuilding("crm", "/crm");
    enterpriseEventBus.openProduction("reels");
    expect(seen).toBe(1);
    expect(enterpriseEventBus.recent(5).length).toBeGreaterThanOrEqual(3);
    unsub();
  });

  it("syncs shared context from route", () => {
    const ctx = useIntegrationContext.getState().syncFromRoute("/production-studio");
    expect(ctx.surface).toBe("production");
    expect(ctx.moduleId).toBe("production");
    expect(useIntegrationContext.getState().path).toBe("/production-studio");
  });

  it("registers universal search covering production and city", () => {
    registerIntegrationSearch();
    const hits = searchProvider.search("reels");
    expect(hits.some((h) => h.path.includes("production") || h.title.toLowerCase().includes("reels"))).toBe(true);
    const city = searchProvider.search("enterprise city");
    expect(city.some((h) => h.path.includes("enterprise-city") || h.path.includes("/city"))).toBe(true);
  });

  it("restores session via coordinator", () => {
    const report = sessionCoordinator.restoreAll();
    expect(report.version).toBe("28.0");
    expect(report.lastModule).toBeTruthy();
    expect(sessionCoordinator.isRestored()).toBe(true);
    const again = sessionCoordinator.restoreAll();
    expect(again.desktop).toBe(report.desktop);
  });
});
