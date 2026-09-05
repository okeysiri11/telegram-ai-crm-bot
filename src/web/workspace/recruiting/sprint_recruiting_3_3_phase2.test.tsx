import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AdsControlCenterPage } from "./AdsControlCenterPage";

const fetchMock = vi.fn(async (url: string) => {
  const u = String(url);
  if (u.includes("/oauth/start")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: false, error: "NOT_CONFIGURED", message_ru: "Не задан app/client identifier." }),
    };
  }
  if (u.includes("/ads/control-center")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        providers: { meta: { status: "not_connected" }, google: { status: "not_connected" }, tiktok: { status: "not_connected" } },
        overview: { connected_providers: 0, spend: null, impressions: null, clicks: null, no_live_data: true, data_source: { spend: "UNAVAILABLE" } },
        kpis: { spend: null, applications: 0 },
        provider_connect: [
          {
            provider: "meta",
            label: "Meta Ads",
            status: "NOT_CONFIGURED",
            connected: false,
            button_ru: "Подключить Meta Ads",
            message_ru: "Для подключения Meta Ads задайте META_ADS_APP_ID и META_ADS_APP_SECRET.",
            wizard_progress: {
              steps: [
                { id: "prerequisites", label_ru: "Предварительные условия", current: true },
                { id: "authorize", label_ru: "Авторизация" },
              ],
            },
          },
        ],
        traffic: { excluded_test_leads: 0 },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
});

vi.stubGlobal("fetch", fetchMock);

describe("Recruiting 3.3 Phase 2 provider wizard", () => {
  beforeEach(() => fetchMock.mockClear());

  it("shows connect CTA and missing-config explanation instead of a dead button", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/ads?embed=1&section=providers"]}>
        <Routes>
          <Route path="/workspace/recruiting/ads" element={<AdsControlCenterPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("ads-connect-meta")).toBeTruthy();
    expect(screen.getByTestId("ads-wizard-meta").textContent).toContain("Предварительные условия");
    fireEvent.click(screen.getByText("Подключить Meta Ads"));
    expect((await screen.findByTestId("ads-connect-hint")).textContent).toMatch(/не задан|META_ADS/i);
    expect(screen.getByTestId("ads-connect-meta").textContent).toContain("NOT_CONFIGURED");
  });
});
