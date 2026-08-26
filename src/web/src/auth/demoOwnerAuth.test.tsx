import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  DEMO_PASSWORD,
  isDemoAuthEnabled,
  isGoogleAuthConfigured,
  loginViaDemoAuth,
  OWNER_DEMO_EMAIL,
  OWNER_DEMO_TENANT,
  OWNER_PERMISSIONS,
  resolveDemoAuthEnabled,
} from "@/auth/demoAuthProvider";
import { productionLogin, productionRegister } from "@/auth/identityApi";
import { useAuthStore } from "@/auth/authStore";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
import { PermissionGuard } from "@/shell/PermissionGuard";
import { openOwnerDemoWorkspace } from "@/multi-role/applyDemoSession";
import { VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";
import { isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { isRouteAllowedForViewMode } from "@/ux-revolution";
import { wsKey } from "@/multi-role/workspaceSlot";
import { LoginPage } from "../../auth/pages/LoginPage";
import { CasinoApp } from "@/casino/CasinoApp";

function fetchCalledIsam(spy: { mock: { calls: unknown[][] } }): boolean {
  return spy.mock.calls.some((call) => {
    const url = String(call[0] ?? "");
    return (
      url.includes("enterprise-isam") ||
      url.includes("localhost:8080") ||
      url.includes("/management/identity")
    );
  });
}

const OWNER_VERTICAL_ROUTES = [
  "/workspace/crypto",
  "/workspace/beauty",
  "/workspace/cafe",
  "/workspace/agro",
  "/workspace/drone",
  "/workspace/legal",
  "/vertical/travel",
  "/command-center",
  "/creative-factory",
  "/owner",
  "/dashboard",
  "/settings",
  "/admin",
  "/casino",
] as const;

const CASINO_UI_ROUTES = [
  "/casino",
  "/casino/lobby",
  "/casino/map",
  "/casino/roulette",
  "/casino/roulette/table/royale-1",
  "/casino/blackjack",
  "/casino/poker",
  "/casino/slots",
  "/casino/vip",
  "/casino/bar",
  "/casino/restaurant",
] as const;

const ERROR_COPY = [
  "authentication backend unavailable",
  "Google authentication unavailable",
  "зал не найден",
  "ISAM proxy",
];

function pageHasAuthFailure(container: HTMLElement): boolean {
  const text = container.textContent?.toLowerCase() || "";
  return ERROR_COPY.some((msg) => text.includes(msg.toLowerCase()));
}

describe("Canonical Owner auth", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      authMode: null,
      accessExpiresAt: null,
    });
  });

  it("enables demo auth in test/dev and never in production", () => {
    expect(isDemoAuthEnabled()).toBe(true);
    expect(resolveDemoAuthEnabled({ PROD: true, DEV: false, VITE_DEMO_AUTH: "true" })).toBe(false);
    expect(isGoogleAuthConfigured()).toBe(false);
  });

  it("logs in owner@ados.demo without calling ISAM", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const session = await productionLogin(OWNER_DEMO_EMAIL, DEMO_PASSWORD, OWNER_DEMO_TENANT);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(session.user.email).toBe(OWNER_DEMO_EMAIL);
    expect(session.user.roleId).toBe("platform_owner");
    expect(session.user.tenantId).toBe("ados");
    expect(session.user.permissions).toEqual(expect.arrayContaining(["admin", "super_admin", "all"]));
    fetchSpy.mockRestore();
  });

  it("rejects the wrong demo password", () => {
    expect(() => loginViaDemoAuth(OWNER_DEMO_EMAIL, "wrong", OWNER_DEMO_TENANT)).toThrow(/rejected/i);
  });

  it("grants owner full permissions and vertical access", () => {
    const session = loginViaDemoAuth(OWNER_DEMO_EMAIL, DEMO_PASSWORD, "demo-corp");
    expect(session.user.tenantId).toBe("ados");
    for (const permission of OWNER_PERMISSIONS) {
      expect(session.user.permissions).toContain(permission);
    }
    expect(session.user.roles).toEqual(
      expect.arrayContaining(["owner", "platform_owner", "super_admin"]),
    );
    expect(isFirstEntryComplete()).toBe(true);
    for (const vertical of VERTICAL_WORKSPACES) {
      const route = vertical.legacyRoute || vertical.route;
      expect(isRouteAllowedForViewMode(route, "platform_owner")).toBe(true);
    }
  });

  it("opens owner workspace without ISAM", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const creds = openOwnerDemoWorkspace();
    expect(creds).toEqual({ email: OWNER_DEMO_EMAIL, password: DEMO_PASSWORD, tenantId: OWNER_DEMO_TENANT });
    await useAuthStore.getState().login(creds.email, creds.password, creds.tenantId);
    expect(fetchCalledIsam(fetchSpy)).toBe(false);
    expect(useAuthStore.getState().user?.roleId).toBe("platform_owner");
    fetchSpy.mockRestore();
  });

  it("preserves demo session on refresh and destroys it on logout", async () => {
    await useAuthStore.getState().login(OWNER_DEMO_EMAIL, DEMO_PASSWORD, OWNER_DEMO_TENANT);
    const refreshed = await useAuthStore.getState().refreshSession();
    expect(refreshed).toBe(true);
    expect(useAuthStore.getState().user?.email).toBe(OWNER_DEMO_EMAIL);
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
    expect(localStorage.getItem(wsKey("ewp_session_v1"))).toBeNull();
  });

  it("redirects unauthenticated users to login", () => {
    render(
      <MemoryRouter initialEntries={["/owner"]}>
        <Routes>
          <Route path="/login" element={<p>login-gate</p>} />
          <Route
            path="/owner"
            element={
              <ProtectedRoute>
                <p>owner-home</p>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("login-gate")).toBeTruthy();
    expect(screen.queryByText("owner-home")).toBeNull();
  });

  it("lets platform owner through permission and vertical routes", async () => {
    await useAuthStore.getState().login(OWNER_DEMO_EMAIL, DEMO_PASSWORD, OWNER_DEMO_TENANT);
    render(
      <MemoryRouter>
        <PermissionGuard require={["admin", "crm", "crypto"]}>
          <p>owner-ok</p>
        </PermissionGuard>
      </MemoryRouter>,
    );
    expect(screen.getByText("owner-ok")).toBeTruthy();
    for (const route of OWNER_VERTICAL_ROUTES) {
      expect(isRouteAllowedForViewMode(route, "platform_owner")).toBe(true);
    }
  });

  it("does not attempt demo registration against ISAM", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    await expect(
      productionRegister({ email: "new@ados.demo", password: "longpass1", tenantId: "ados" }),
    ).rejects.toThrow(/демо-режиме/i);
    expect(fetchCalledIsam(fetchSpy)).toBe(false);
    fetchSpy.mockRestore();
  });

  it("renders login form for canonical owner without Google or account picker", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    expect((screen.getByRole("textbox") as HTMLInputElement).value).toBe(OWNER_DEMO_EMAIL);
    expect(screen.queryByText("Продолжить через Google")).toBeNull();
    expect(screen.queryByText("owner@demo.corp")).toBeNull();
    expect(screen.queryByLabelText("Демо-аккаунты")).toBeNull();
    expect(screen.queryByText("Создать аккаунт")).toBeNull();
    expect(screen.getByRole("button", { name: "Войти по Email" })).toBeTruthy();
  });

  it("submits email login and lands on /owner", async () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/owner" element={<p>owner-home</p>} />
        </Routes>
      </MemoryRouter>,
    );
    const password = document.querySelector('input[type="password"]') as HTMLInputElement;
    fireEvent.change(password, { target: { value: DEMO_PASSWORD } });
    fireEvent.click(screen.getByRole("button", { name: "Войти по Email" }));
    expect(await screen.findByText("owner-home")).toBeTruthy();
    expect(useAuthStore.getState().user?.email).toBe(OWNER_DEMO_EMAIL);
    expect(useAuthStore.getState().user?.tenantId).toBe("ados");
  });

  it("honors returnTo after login", async () => {
    render(
      <MemoryRouter initialEntries={["/login?returnTo=/casino/roulette/table/royale-1"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/casino/roulette/table/royale-1" element={<p>roulette-table</p>} />
        </Routes>
      </MemoryRouter>,
    );
    const password = document.querySelector('input[type="password"]') as HTMLInputElement;
    fireEvent.change(password, { target: { value: DEMO_PASSWORD } });
    fireEvent.click(screen.getByRole("button", { name: "Войти по Email" }));
    expect(await screen.findByText("roulette-table")).toBeTruthy();
  });

  it("renders casino rooms for authenticated owner without unknown-hall copy", async () => {
    await useAuthStore.getState().login(OWNER_DEMO_EMAIL, DEMO_PASSWORD, OWNER_DEMO_TENANT);
    for (const path of CASINO_UI_ROUTES) {
      const view = render(
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/casino/*" element={<CasinoApp />} />
          </Routes>
        </MemoryRouter>,
      );
      await waitFor(() => expect(view.container.textContent?.trim().length, path).toBeGreaterThan(0));
      expect(pageHasAuthFailure(view.container), path).toBe(false);
      view.unmount();
    }
  });
});
