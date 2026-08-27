/**
 * Sprint Recruiting 1.8 — Provider Connections + Advertising Control Center.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { AdsControlCenterPage } from "./AdsControlCenterPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 200, json: async () => ({ ok: true, item: { id: "x1", recommendation: "pause_campaign", status: "PENDING", approval_required: true } }) };
  }
  if (u.includes("/providers")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        items: [
          {
            provider: "meta",
            label: "Meta Ads",
            status: "NOT_CONFIGURED",
            status_label_ru: "Не настроено",
            mode: "LIVE",
            mode_label_ru: "LIVE",
            connection_type: "OAuth / access token",
            account_id: null,
            last_successful_health_check: null,
            last_error: null,
            credential_presence: { present: false, fields: { access_token: { present: false } } },
            credential_expiry: null,
            scopes: [],
            tracking_status: "WAITING_PROVIDER",
            mock: false,
            wizard: [{ id: "access_token", label_ru: "Токен доступа", secret: true }],
          },
        ],
      }),
    };
  }
  if (u.includes("/ads/control-center")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        connected: false,
        providers: { meta: { status: "not_connected" } },
        overview: {
          connected_providers: 0,
          spend: null,
          impressions: null,
          clicks: null,
          leads: 2,
          no_live_data: true,
          message_ru: "Нет живых данных",
        },
        campaigns: [],
        funnel: { steps: [{ id: "lead", label_ru: "Лид", count: 2 }] },
        attribution: { first_touch: { source: "meta" }, last_touch: { source: "google" } },
        source_analytics: { items: [] },
        automation: { items: [], approval_required_default: true },
        ai_optimization: { items: [], advisory_only: true, live_write_access: false },
        provider_health: { infra_independent: true, items: [] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

describe("Provider Connections", () => {
  beforeEach(() => fetchMock.mockClear());

  it("renders cards, health states and configure dialog without secrets", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/integrations?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/integrations" element={<ProviderConnectionsPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("provider-connections-page")).toBeTruthy();
    expect(screen.getByTestId("provider-card-meta").textContent).toContain("Не настроено");
    expect(screen.getByTestId("provider-card-meta").textContent).toContain("LIVE");
    fireEvent.click(screen.getByText("Настроить"));
    expect(screen.getByText("Секреты не сохраняются в браузере.")).toBeTruthy();
  });
});

describe("Advertising Control Center", () => {
  beforeEach(() => fetchMock.mockClear());

  it("shows sections, no live provider data, automation approval and advisory AI", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/ads?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/ads" element={<AdsControlCenterPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("ads-control-center-page")).toBeTruthy();
    expect(screen.getByTestId("ads-sections").textContent).toContain("Провайдеры");
    expect(screen.getByTestId("ads-sections").textContent).toContain("AI-оптимизация");
    expect(screen.getByTestId("ads-no-live-data").textContent).toContain("Нет живых данных");
    fireEvent.click(screen.getByText("Автоматизация"));
    expect(await screen.findByTestId("ads-automation-approval")).toBeTruthy();
    fireEvent.click(screen.getByText("AI-оптимизация"));
    expect((await screen.findByTestId("ads-ai-advisory")).textContent).toContain("консультатив");
  });
});
