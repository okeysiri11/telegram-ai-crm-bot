import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AdsControlCenterPage } from "./AdsControlCenterPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST" && u.includes("/spend")) {
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        item: { id: "sp1", amount: 80, currency: "EUR", label_ru: "Расход внесён оператором", entered_by: "platform_owner", provider_synced: false },
      }),
    };
  }
  if (init?.method === "POST" && u.includes("/campaigns")) {
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        item: {
          id: "cmp-1",
          name: "Vanguard Instagram Estonia TEST",
          source: "instagram",
          source_label_ru: "Instagram",
          status: "ACTIVE",
          country: "EE",
          program: "logistics",
          origin_label_ru: "Внутренняя кампания — рекламный кабинет не подключён.",
        },
      }),
    };
  }
  if (u.includes("/campaigns/cmp-1")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        item: { id: "cmp-1", name: "Vanguard Instagram Estonia TEST" },
        campaign: { id: "cmp-1", name: "Vanguard Instagram Estonia TEST" },
        origin_label_ru: "Внутренняя кампания — рекламный кабинет не подключён.",
        funnel: {
          steps: [
            { id: "impressions", label_ru: "Показы", count: null, conversion_from_previous: null, conversion_overall: null },
            { id: "applications", label_ru: "Заявки", count: 0, conversion_from_previous: null, conversion_overall: null },
            { id: "hired", label_ru: "Наняты", count: 0, conversion_from_previous: null, conversion_overall: null },
          ],
        },
        recruiters: [{ recruiter_label: "Не назначен", assigned_candidates: 0, qualified: 0, interviews: 0, approved: 0, hired: 0 }],
        spend_entries: [{ id: "sp1", amount: 80, currency: "EUR", label_ru: "Расход внесён оператором", entered_by: "owner" }],
      }),
    };
  }
  if (u.includes("/providers/") && u.includes("/oauth/start")) {
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
        connected: false,
        title_ru: "РЕКЛАМА VANGUARD",
        providers: { meta: { status: "not_connected" }, google: { status: "not_connected" }, tiktok: { status: "not_connected" } },
        overview: {
          connected_providers: 0,
          spend: 80,
          impressions: null,
          clicks: null,
          leads: 0,
          no_live_data: true,
          message_ru: "Нет живых данных",
          data_source: { spend: "OPERATOR_MANUAL", cost_per_lead: "UNAVAILABLE" },
        },
        kpis: { spend: 80, applications: 0, cpl: null, qualified: 0, interviews: 0, approved: 0, hired: 0, cost_per_hire: null },
        campaigns: [
          {
            id: "cmp-1",
            name: "Vanguard Instagram Estonia TEST",
            source: "instagram",
            source_label_ru: "Instagram",
            provider_backed: true,
            status: "ACTIVE",
            utm_source: "instagram",
            utm_medium: "paid_social",
            utm_campaign: "ee_ig",
            spend: 80,
            applications: 0,
            cpl: null,
            qualified: 0,
            interviews: 0,
            approved: 0,
            hired: 0,
            cost_per_hire: null,
            conversion: null,
          },
        ],
        funnel: { steps: [{ id: "lead", label_ru: "Лид", count: 0 }] },
        attribution: { first_touch: { source: "instagram" }, last_touch: { source: "instagram" } },
        source_analytics: { items: [] },
        source_economics: [{ source: "instagram", label_ru: "Instagram", applications: 0, spend: 80, cpl: null, hired: 0 }],
        automation: { items: [], approval_required_default: true },
        ai_optimization: { items: [], advisory_only: true, live_write_access: false },
        provider_health: { infra_independent: true, items: [] },
        provider_connect: [
          { provider: "meta", label: "Meta Ads", status: "NOT_CONFIGURED", connected: false, button_ru: "Подключить Meta Ads" },
        ],
        traffic: { excluded_test_leads: 8, excluded_test_candidates: 5 },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function renderAds(path = "/workspace/recruiting/ads?embed=1") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/workspace/recruiting/ads" element={<AdsControlCenterPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Recruiting 3.3 Advertising Control Center", () => {
  beforeEach(() => fetchMock.mockClear());

  it("renders KPI empty-honest states and TEST exclusion", async () => {
    renderAds();
    expect(await screen.findByTestId("ads-control-center-page")).toBeTruthy();
    expect(screen.getByTestId("ads-kpi-cards").textContent).toContain("Расход");
    expect(screen.getByTestId("ads-kpi-cpl").textContent).toContain("Нет живых данных");
    expect(screen.getByTestId("ads-no-live-data").textContent).toContain("Нет живых данных");
    expect(screen.getByTestId("ads-test-exclusion").textContent).toContain("8");
    expect(screen.getByTestId("ads-date-filters").textContent).toContain("Сегодня");
  });

  it("shows campaign table and internal campaign copy", async () => {
    renderAds("/workspace/recruiting/ads?embed=1&section=campaigns");
    expect(await screen.findByTestId("ads-campaign-form")).toBeTruthy();
    expect(screen.getByTestId("ads-internal-note").textContent).toContain("рекламный кабинет не подключён");
    expect(screen.getByText("Vanguard Instagram Estonia TEST")).toBeTruthy();
    expect(screen.getByText("НЕ ПОДКЛЮЧЕНО")).toBeTruthy();
  });

  it("opens campaign detail and records operator spend", async () => {
    renderAds("/workspace/recruiting/ads?embed=1&section=campaigns");
    fireEvent.click(await screen.findByText("Vanguard Instagram Estonia TEST"));
    expect(await screen.findByTestId("ads-campaign-detail")).toBeTruthy();
    expect(screen.getByTestId("ads-campaign-funnel").textContent).toContain("Показы");
    expect(screen.getByTestId("ads-manual-spend").textContent).toContain("Расход внесён оператором");
    fireEvent.change(screen.getAllByPlaceholderText("Сумма")[0], { target: { value: "80" } });
    fireEvent.click(screen.getByText("Внести расход"));
    expect(await screen.findByTestId("ads-spend-history")).toBeTruthy();
  });

  it("keeps provider connect buttons from becoming CONNECTED", async () => {
    renderAds("/workspace/recruiting/ads?embed=1&section=providers");
    expect(await screen.findByTestId("ads-connect-meta")).toBeTruthy();
    expect(screen.getByTestId("ads-connect-meta").textContent).toContain("NOT_CONFIGURED");
    fireEvent.click(screen.getByText("Подключить Meta Ads"));
    expect((await screen.findByTestId("ads-connect-hint")).textContent).toMatch(/не настроен|не задан/i);
    expect(screen.getByTestId("ads-provider-meta").textContent).toContain("not_connected");
  });
});
