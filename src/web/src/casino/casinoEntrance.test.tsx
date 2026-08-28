import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { casinoSound } from "./casinoSound";
import { loginRedirect, sanitizeReturnTo } from "@/navigation/safeReturnTo";
import { ENTRANCE_PREVIEWS } from "./entrance/CasinoGamePreviewStrip";

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casino/*" element={<CasinoApp />} />
        <Route path="/enterprise-city" element={<p data-testid="city-page">Odessa City</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function mockReducedMotion(enabled: boolean) {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) =>
    ({
      matches: enabled && String(query).includes("prefers-reduced-motion"),
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
  return () => {
    window.matchMedia = original;
  };
}

describe("Sprint 21 Odessa Prime cinematic entrance", () => {
  afterEach(() => {
    casinoSound.setMuted(true);
  });

  it("renders CasinoShell on /casino without enterprise CRM chrome", async () => {
    const view = mount("/casino");
    await waitFor(() => expect(screen.getByTestId("casino-shell")).toBeTruthy(), { timeout: 15000 });
    expect(screen.getByTestId("casino-entrance")).toBeTruthy();
    expect(screen.getByLabelText("Odessa Prime Casino")).toBeTruthy();
    expect(screen.getAllByText("ГОРОД").length).toBeGreaterThan(0);
    expect(screen.getAllByText("КАЗИНО").length).toBeGreaterThan(0);
    expect(screen.getAllByText("АКЦИИ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("VIP").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ТУРНИРЫ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ПОДДЕРЖКА").length).toBeGreaterThan(0);
    expect(screen.queryByText("Enterprise Dashboard")).toBeNull();
    expect(screen.queryByTestId("mobile-favorites-row")).toBeNull();
    expect(document.querySelector(".ados-shell")).toBeNull();
    view.unmount();
  }, 20000);

  it("renders cinematic hero, facade, CTA and status panels", () => {
    const view = mount("/casino");
    expect(screen.getByTestId("casino-entrance")).toBeTruthy();
    expect(screen.getByTestId("casino-hero")).toBeTruthy();
    expect(screen.getByTestId("casino-facade")).toBeTruthy();
    expect(view.container.querySelector(".op-marble")).toBeTruthy();
    expect(view.container.querySelector(".op-brass-arch")).toBeTruthy();
    expect(view.container.querySelector(".op-runner")).toBeTruthy();
    expect(screen.getByText("Добро пожаловать в мир азарта и роскоши")).toBeTruthy();
    expect(screen.getByText("ИГРАЙТЕ НА DEMO CHIPS")).toBeTruthy();
    expect(screen.getByTestId("casino-enter-cta")).toHaveTextContent("ВОЙТИ В КАЗИНО");
    expect(screen.getByTestId("casino-status-panels")).toBeTruthy();
    expect(screen.getByText("LIVE ИГРОКИ")).toBeTruthy();
    expect(screen.getByText("128")).toBeTruthy();
    expect(screen.getByText("DEMO БАЛАНС")).toBeTruthy();
    expect(screen.getByText("JACKPOT")).toBeTruthy();
    view.unmount();
  });

  it("navigates ВОЙТИ В КАЗИНО into the lobby after the entrance transition", async () => {
    const view = mount("/casino");
    await waitFor(() => expect(screen.getByTestId("casino-enter-cta")).toBeTruthy(), { timeout: 15000 });
    fireEvent.click(screen.getByTestId("casino-enter-cta"));
    expect(screen.getByTestId("casino-enter-veil")).toBeTruthy();
    expect(await screen.findByTestId("casino-lobby", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("renders six game preview cards with artwork", () => {
    const view = mount("/casino");
    expect(screen.getByTestId("casino-preview-strip")).toBeTruthy();
    for (const card of ENTRANCE_PREVIEWS) {
      const node = screen.getByTestId(`preview-${card.id}`);
      expect(node).toBeTruthy();
      expect(node.querySelector(".op-preview-svg")).toBeTruthy();
      expect(node).toHaveTextContent(card.title);
    }
    view.unmount();
  });

  it("navigates a live preview card to its canonical room", async () => {
    const view = mount("/casino");
    fireEvent.click(screen.getByTestId("preview-roulette"));
    expect(await screen.findByTestId("roulette-table")).toBeTruthy();
    view.unmount();
  });

  it("opens Скоро feedback for an unimplemented preview card", () => {
    const view = mount("/casino");
    fireEvent.click(screen.getByTestId("preview-live"));
    expect(screen.getByTestId("casino-soon-modal")).toBeTruthy();
    expect(screen.getByText("Скоро")).toBeTruthy();
    fireEvent.click(screen.getByText("ПОНЯТНО"));
    expect(screen.queryByTestId("casino-soon-modal")).toBeNull();
    view.unmount();
  });

  it("sends В ГОРОД to the Odessa city experience", async () => {
    const view = mount("/casino");
    fireEvent.click(screen.getByTestId("casino-to-city"));
    expect(await screen.findByTestId("city-page")).toBeTruthy();
    view.unmount();
  });

  it("keeps sound muted by default", () => {
    const view = mount("/casino");
    expect(casinoSound.muted).toBe(true);
    const toggle = screen.getByTestId("casino-sound-toggle");
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    expect(toggle).toHaveAttribute("aria-label", "Включить звук");
    view.unmount();
  });

  it("skips the cinematic veil when prefers-reduced-motion is set", async () => {
    const restore = mockReducedMotion(true);
    const view = mount("/casino");
    fireEvent.click(screen.getByTestId("casino-enter-cta"));
    expect(screen.queryByTestId("casino-enter-veil")).toBeNull();
    expect(await screen.findByTestId("casino-lobby")).toBeTruthy();
    restore();
    view.unmount();
  });

  it("preserves casino returnTo for auth", () => {
    expect(sanitizeReturnTo("/casino")).toBe("/casino");
    expect(sanitizeReturnTo("/casino/lobby")).toBe("/casino/lobby");
    expect(loginRedirect("/casino")).toContain("returnTo=");
    expect(decodeURIComponent(loginRedirect("/casino"))).toContain("/casino");
  });

  it("keeps unknown halls and deep-links inside CasinoShell", async () => {
    const unknown = mount("/casino/missing-hall");
    expect(await screen.findByTestId("casino-unknown")).toBeTruthy();
    expect(screen.getByText("Зал не найден")).toBeTruthy();
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    unknown.unmount();

    const deep = mount("/casino/roulette/table/royale-1");
    expect(await screen.findByTestId("roulette-table")).toBeTruthy();
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    deep.unmount();
  });

  it("keeps a compact mobile nav and large enter CTA", () => {
    const view = mount("/casino");
    expect(view.container.querySelector(".op-bottom")).toBeTruthy();
    expect(screen.getByTestId("casino-enter-cta")).toBeTruthy();
    expect(screen.getByTestId("casino-preview-strip")).toBeTruthy();
    view.unmount();
  });
});
