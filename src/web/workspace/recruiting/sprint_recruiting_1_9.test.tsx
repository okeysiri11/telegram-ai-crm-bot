/**
 * Sprint Recruiting 1.9 — live provider UI: OAuth, LIVE/MOCK, approvals.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { AdsControlCenterPage } from "./AdsControlCenterPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/oauth/start")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, authorize_url: "https://example.test/oauth" }) };
  }
  if (init?.method === "POST") {
    return { ok: true, status: 200, json: async () => ({ ok: true, item: { id: "x1", status: "PENDING", approval_required: true } }) };
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
            oauth_ready: true,
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
        overview: { no_live_data: true, spend: null, data_source: { spend: "UNAVAILABLE", leads: "INTERNAL", cost_per_lead: "UNAVAILABLE" } },
        campaign_writes: { items: [{ id: "w1", action: "pause", status: "ACTION_PENDING_APPROVAL" }], approval_required: true },
        outbound_messages: { items: [{ id: "m1", channel: "telegram", status: "WAITING_PROVIDER" }] },
        ai_optimization: { items: [], advisory_only: true, live_write_access: false },
        automation: { items: [], approval_required_default: true },
        providers: { meta: { status: "not_connected" } },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function withinSections(root: HTMLElement, label: string) {
  return Array.from(root.querySelectorAll("button")).find((el) => el.textContent === label) as HTMLElement;
}

describe("Provider Connections live UI", () => {
  beforeEach(() => fetchMock.mockClear());

  it("shows OAuth connect and LIVE vs not configured", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/integrations?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/integrations" element={<ProviderConnectionsPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("provider-connections-page")).toBeTruthy();
    expect(screen.getByTestId("provider-card-meta").textContent).toContain("LIVE");
    expect(screen.getByTestId("provider-oauth-meta").textContent).toContain("Подключить");
  });

  it("shows oauth result states", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/integrations?embed=1&oauth=meta&status=error"]}>
        <Routes>
          <Route path="/workspace/recruiting/integrations" element={<ProviderConnectionsPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect((await screen.findByTestId("oauth-flow-status")).textContent).toContain("Ошибка подключения");
  });
});

describe("Advertising Control Center live UI", () => {
  beforeEach(() => fetchMock.mockClear());

  it("shows unavailable live data and approval surfaces", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/ads?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/ads" element={<AdsControlCenterPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("ads-control-center-page")).toBeTruthy();
    expect(screen.getByTestId("ads-no-live-data").textContent).toContain("Нет живых данных");
    expect(screen.getByTestId("ads-data-sources").textContent).toContain("UNAVAILABLE");
    const sections = screen.getByTestId("ads-sections");
    fireEvent.click(sections.querySelector("button:nth-child(3)") as HTMLElement);
    expect((await screen.findByTestId("ads-campaign-approval")).textContent).toContain("согласовани");
    fireEvent.click(withinSections(sections, "Лиды"));
    expect((await screen.findByTestId("ads-messaging-approval")).textContent).toContain("WAITING_PROVIDER");
    fireEvent.click(withinSections(sections, "AI-оптимизация"));
    expect((await screen.findByTestId("ads-ai-advisory")).textContent).toContain("консультатив");
  });
});
