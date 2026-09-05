/**
 * Sprint 3.3.2 — Provider connection UI must open without crashing the Ads view.
 */

import type { ReactElement } from "react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AdsControlCenterPage } from "./AdsControlCenterPage";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { ProviderConnectionBoundary } from "./ProviderConnectionBoundary";
import { PROVIDER_WIZARD_LOAD_ERROR_RU } from "./providerConnectionCopy";

const providerItems = [
  {
    provider: "meta",
    label: "Meta Ads",
    status: "NOT_CONFIGURED",
    status_label_ru: "Не настроено",
    connect_cta: true,
    oauth_ready: false,
  },
  {
    provider: "google",
    label: "Google Ads",
    status: "NOT_CONFIGURED",
    status_label_ru: "Не настроено",
    connect_cta: true,
    oauth_ready: false,
  },
  {
    provider: "tiktok",
    label: "TikTok Ads",
    status: "NOT_CONFIGURED",
    status_label_ru: "Не настроено",
    connect_cta: true,
    oauth_ready: false,
  },
  {
    provider: "whatsapp",
    label: "WhatsApp",
    status: "NOT_CONFIGURED",
    tracking_status: "WAITING_PROVIDER",
    status_label_ru: "Ожидает провайдера",
  },
  {
    provider: "telegram",
    label: "Telegram",
    status: "DISABLED",
    frozen: true,
    message_ru: "Telegram намеренно отключён.",
  },
];

const fetchMock = vi.fn(async (url: string) => {
  const u = String(url);
  if (u.includes("/oauth/start")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: false, error: "NOT_CONFIGURED", message_ru: "Не задан app/client identifier." }),
    };
  }
  if (u.includes("/providers/") && u.includes("/diagnostics")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, provider: "meta", secrets: false }) };
  }
  if (u.includes("/providers")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: providerItems }) };
  }
  if (u.includes("/ads/control-center")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        providers: {
          meta: { status: "NOT_CONFIGURED" },
          google: { status: "NOT_CONFIGURED" },
          tiktok: { status: "NOT_CONFIGURED" },
        },
        overview: { connected_providers: 0, spend: null, impressions: null, clicks: null, no_live_data: true },
        kpis: { spend: null, applications: 0 },
        provider_connect: [
          { provider: "meta", label: "Meta Ads", status: "NOT_CONFIGURED", connected: false, button_ru: "Подключить Meta Ads" },
          { provider: "google", label: "Google Ads", status: "NOT_CONFIGURED", connected: false, button_ru: "Подключить Google Ads" },
          { provider: "tiktok", label: "TikTok Ads", status: "NOT_CONFIGURED", connected: false, button_ru: "Подключить TikTok Ads" },
        ],
        traffic: { excluded_test_leads: 0 },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
});

vi.stubGlobal("fetch", fetchMock);

function renderAdsProviders() {
  return render(
    <MemoryRouter initialEntries={["/workspace/recruiting/ads?embed=1&section=providers"]}>
      <Routes>
        <Route path="/workspace/recruiting/ads" element={<AdsControlCenterPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Recruiting 3.3.2 provider connection UI", () => {
  beforeEach(() => fetchMock.mockClear());

  it("renders the providers page and keeps statuses NOT_CONFIGURED", async () => {
    renderAdsProviders();
    expect(await screen.findByTestId("ads-control-center-page")).toBeTruthy();
    expect(screen.getByTestId("ads-open-connections")).toBeTruthy();
    expect(screen.getByTestId("ads-connect-meta").textContent).toContain("NOT_CONFIGURED");
    expect(screen.getByTestId("ads-connect-google").textContent).toContain("NOT_CONFIGURED");
    expect(screen.getByTestId("ads-connect-tiktok").textContent).toContain("NOT_CONFIGURED");
    expect(screen.getAllByText("Переподключить").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Диагностика").length).toBeGreaterThan(0);
  });

  it("opens the connection wizard in-place without a module-load crash", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    renderAdsProviders();
    fireEvent.click(await screen.findByTestId("ads-open-connections"));
    expect(await screen.findByTestId("ads-connections-wizard")).toBeTruthy();
    expect(screen.getByTestId("ads-wizard-missing-meta").textContent).toContain("META_ADS_APP_ID");
    expect(screen.getByTestId("ads-wizard-missing-google").textContent).toContain("GOOGLE_ADS_CLIENT_ID");
    expect(screen.getByTestId("ads-wizard-missing-tiktok").textContent).toContain("TIKTOK_ADS_APP_ID");
    fireEvent.click(screen.getByRole("button", { name: "Meta Ads" }));
    expect((await screen.findByTestId("ads-wizard-connect-hint")).textContent).toContain("META_ADS_APP_ID");
    expect(assign).not.toHaveBeenCalled();
    expect(screen.queryByText("This view failed to render")).toBeNull();
  });

  it("renders the integrations provider page with missing-config copy", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/integrations?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/integrations" element={<ProviderConnectionsPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("provider-connections-page")).toBeTruthy();
    expect(screen.getByTestId("provider-missing-config-meta").textContent).toContain("META_ADS_APP_ID");
    expect(screen.getByTestId("provider-card-meta").textContent).toMatch(/NOT_CONFIGURED|Не настроено/);
    expect(screen.getByTestId("telegram-frozen-badge")).toBeTruthy();
    expect(screen.getAllByText("Переподключить").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Диагностика").length).toBeGreaterThan(0);
  });

  it("keeps a module-load failure inside the local fallback", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    function Boom(): ReactElement {
      throw new Error("Importing a module script failed.");
    }
    render(
      <ProviderConnectionBoundary>
        <Boom />
      </ProviderConnectionBoundary>,
    );
    expect(screen.getByTestId("provider-connection-fallback").textContent).toContain(
      PROVIDER_WIZARD_LOAD_ERROR_RU.split("\n")[0],
    );
    expect(screen.getByTestId("provider-connection-retry")).toBeTruthy();
    expect(screen.getByTestId("provider-connection-reload")).toBeTruthy();
    expect(screen.queryByText("This view failed to render")).toBeNull();
    expect(screen.queryByText("Reliability")).toBeNull();
    spy.mockRestore();
  });
});

describe("Recruiting 3.3.2 local fallback retry", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("retry remounts children after a render failure", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    let shouldThrow = true;
    function Flaky(): ReactElement {
      if (shouldThrow) throw new Error("Importing a module script failed.");
      return <p data-testid="provider-wizard-recovered">Мастер</p>;
    }
    render(
      <ProviderConnectionBoundary>
        <Flaky />
      </ProviderConnectionBoundary>,
    );
    expect(screen.getByTestId("provider-connection-fallback")).toBeTruthy();
    shouldThrow = false;
    fireEvent.click(screen.getByTestId("provider-connection-retry"));
    expect(screen.getByTestId("provider-wizard-recovered")).toBeTruthy();
    spy.mockRestore();
  });
});
