/**
 * Odessa Prime Casino — first-class platform entry + search cleanup.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, NavLink, Route, Routes } from "react-router-dom";
import { groupsFromPlatformRegistry } from "@/platform-registry/menuCatalog";
import { groupsForMode } from "@/ux-revolution/intelligentNavGroups";
import { searchIndex } from "../../navigation/managers/searchIndex";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { registerIntegrationSearch } from "@/integration-hub/searchRegistration";
import { getBuilding } from "@/enterprise-city/cityCatalog";
import { buildingOps } from "@/enterprise-city/buildingOps";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { applicationRegistry } from "../../navigation/managers/applicationRegistry";
import { CasinoApp } from "./CasinoApp";
import {
  CASINO_CANONICAL_ROUTE,
  CASINO_NAV_ID,
  CASINO_SEARCH_DOC,
  CASINO_SEARCH_ID,
  collapseCasinoSearchHits,
} from "./casinoPlatform";

afterEach(() => {
  cleanup();
});

function businessItems(mode: "simple" | "pro") {
  const groups = groupsFromPlatformRegistry(mode);
  return groups.find((g) => g.id === "business")?.items || [];
}

describe("Odessa Prime Casino platform entry", () => {
  it("adds Casino to left business navigation pointing at /casino", () => {
    const simple = businessItems("simple");
    const pro = businessItems("pro");
    const casino = simple.find((i) => i.id === CASINO_NAV_ID) || pro.find((i) => i.id === CASINO_NAV_ID);
    expect(casino).toBeTruthy();
    expect(casino?.label).toBe("Casino");
    expect(casino?.route).toBe(CASINO_CANONICAL_ROUTE);
    expect(pro.find((i) => i.id === "vert_beauty")?.route).toBe("/workspace/beauty");
    expect(pro.find((i) => i.id === "vert_cafe")?.route).toBe("/workspace/cafe");
    expect(pro.find((i) => i.id === "vert_agro")?.route).toBe("/workspace/agro");
    expect(pro.find((i) => i.id === "vert_drone")?.route).toBe("/workspace/drone");
    expect(pro.find((i) => i.id === "vert_crypto")?.route).toBe("/workspace/crypto");
    const beautyIdx = pro.findIndex((i) => i.id === "vert_beauty");
    const casinoIdx = pro.findIndex((i) => i.id === CASINO_NAV_ID);
    expect(casinoIdx).toBe(beautyIdx + 1);
    const sidebar = groupsForMode("pro").find((g) => g.id === "business")?.items || [];
    expect(sidebar.find((i) => i.id === CASINO_NAV_ID)?.route).toBe(CASINO_CANONICAL_ROUTE);
  });

  it("opens the canonical casino route from the Casino nav item", () => {
    const casino = businessItems("pro").find((i) => i.id === CASINO_NAV_ID);
    expect(casino?.route).toBe("/casino");
    render(
      <MemoryRouter initialEntries={["/workspace/beauty"]}>
        <nav>
          <NavLink to={casino!.route} data-testid={`nav-${CASINO_NAV_ID}`}>
            {casino!.label}
          </NavLink>
          <NavLink to="/workspace/beauty" data-testid="nav-vert_beauty">
            Beauty
          </NavLink>
        </nav>
        <Routes>
          <Route path="/casino/*" element={<p data-testid="casino-canonical-root">Odessa Prime</p>} />
          <Route path="/workspace/beauty" element={<p data-testid="beauty-root">Beauty</p>} />
          <Route path="/workspace/cafe" element={<p data-testid="cafe-root">Cafe</p>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("beauty-root")).toBeTruthy();
    fireEvent.click(screen.getByTestId(`nav-${CASINO_NAV_ID}`));
    expect(screen.getByTestId("casino-canonical-root")).toBeTruthy();
  });

  it("registers one authoritative Odessa Prime Casino search result", () => {
    const docs = searchIndex.list().filter((d) => d.title.toLowerCase().includes("odessa prime casino") || d.id.startsWith("idx_casino"));
    expect(docs).toHaveLength(1);
    expect(docs[0].id).toBe(CASINO_SEARCH_ID);
    expect(docs[0].path).toBe(CASINO_CANONICAL_ROUTE);
    expect(docs[0].status).toBe("AVAILABLE");
    expect(docs[0].kind).toBe("Casino / Entertainment");
    expect(docs[0].action).toBe("Open");
    expect(docs[0].title).toBe("Odessa Prime Casino");
  });

  it("collapses city/waiting duplicate search rows onto the same route", () => {
    const hits = collapseCasinoSearchHits([
      { id: "idx_casino_odessa_prime", title: "Odessa Prime Casino", path: "/casino", status: "AVAILABLE" },
      { id: "idx_casino_lobby", title: "Casino lobby", path: "/casino" },
      { id: "city_casino", title: "Odessa Prime Casino · Enterprise City", path: "/casino/venues/odessa-prime" },
      { id: "hub_city_casino", title: "City · Odessa Prime Casino", path: "/casino/venues/odessa-prime" },
      { id: "other", title: "Beauty", path: "/workspace/beauty" },
    ]);
    const casinoHits = hits.filter((h) => String(h.title).toLowerCase().includes("casino") || String(h.title).toLowerCase().includes("odessa"));
    expect(casinoHits).toHaveLength(1);
    expect(casinoHits[0].path).toBe(CASINO_CANONICAL_ROUTE);
    expect(casinoHits[0].status).toBe("AVAILABLE");
    expect(hits.some((h) => h.path === "/workspace/beauty")).toBe(true);
    const searched = searchProvider.search("odessa prime casino");
    const named = searched.filter((h) => h.title.toLowerCase().includes("odessa prime casino") || h.title.toLowerCase().includes("casino lobby"));
    expect(named).toHaveLength(1);
    expect(named[0].path).toBe("/casino");
    expect(named[0].status).toBe("AVAILABLE");
    expect(named[0].action).toBe("Open");
    registerIntegrationSearch();
    const afterHub = searchProvider
      .search("odessa prime casino")
      .filter((h) => h.title.toLowerCase().includes("odessa prime casino") || h.title.toLowerCase().includes("city · odessa"));
    expect(afterHub).toHaveLength(1);
    expect(afterHub[0].path).toBe("/casino");
    expect(afterHub[0].status).toBe("AVAILABLE");
  });

  it("resolves Enterprise City casino entry to the same canonical route", () => {
    expect(getBuilding("casino")?.route).toBe(CASINO_CANONICAL_ROUTE);
    expect(buildingOps("casino").quickActions[0]?.route).toBe(CASINO_CANONICAL_ROUTE);
    expect(buildingOps("casino").quickActions.some((a) => a.route === "/casino/venues/odessa-prime")).toBe(false);
  });

  it("registers casino in the shared module registry without a second copy", () => {
    const mod = moduleRegistry.get("casino");
    expect(mod?.routes[0]).toBe(CASINO_CANONICAL_ROUTE);
    expect(mod?.navigation[0]?.route).toBe(CASINO_CANONICAL_ROUTE);
    expect(applicationRegistry.get("casino_odessa_prime")?.route).toBe(CASINO_CANONICAL_ROUTE);
  });

  it("opens the existing casino facade on the canonical URL", () => {
    const view = render(
      <MemoryRouter initialEntries={["/casino"]}>
        <Routes>
          <Route path="/casino/*" element={<CasinoApp />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    expect(screen.getByTestId("casino-entrance")).toBeTruthy();
    expect(screen.getByTestId("casino-facade")).toBeTruthy();
    view.unmount();
  });

  it("lazy-loads the casino bundle from the App route", () => {
    const appSrc = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "../App.tsx"), "utf8");
    expect(appSrc).toMatch(/const CasinoApp = lazy\(/);
    expect(appSrc).toMatch(/import\("@\/casino"\)/);
  });

  it("keeps facade door hits invisible with no debug labels", () => {
    const view = render(
      <MemoryRouter initialEntries={["/casino"]}>
        <Routes>
          <Route path="/casino/*" element={<CasinoApp />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(view.container.querySelector("[data-testid='casino-facade-door-hit']")).toBeNull();
    expect(view.container.querySelector(".op-doors")).toBeNull();
    expect(view.container.querySelector(".op-brass-arch")).toBeNull();
    expect(view.container.textContent).not.toContain("HOTSPOT");
    expect(view.container.textContent).not.toContain("debug");
    view.unmount();
  });

  it("keeps other business modules on their existing routes", () => {
    expect(CASINO_SEARCH_DOC.path).toBe("/casino");
    expect(moduleRegistry.get("beauty")?.routes[0]).toBe("/workspace/beauty");
    expect(moduleRegistry.get("cafe")?.routes[0]).toBe("/workspace/cafe");
    expect(moduleRegistry.get("agro")?.routes[0]).toBe("/workspace/agro");
    expect(moduleRegistry.get("drone")?.routes[0]).toBe("/workspace/drone");
    expect(moduleRegistry.get("crypto")?.routes[0]).toBe("/workspace/crypto");
  });
});
