/**
 * Sprint Recruiting 1.5 — advertising control center UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { VanguardProjectPage } from "./VanguardProjectPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (init?.method === "POST") {
    return { ok: true, status: 201, json: async () => ({ ok: true, item: { id: "camp-1", name: "Meta Launch" } }) };
  }
  if (u.includes("/ads/control-center")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        connected: false,
        message_ru: "Провайдер не подключен",
        providers: { meta: { status: "not_connected" }, google: { status: "not_connected" }, tiktok: { status: "not_connected" } },
        source_analytics: { items: [{ source: "meta", leads: 1, candidates: 0, conversion: null }] },
      }),
    };
  }
  if (u.includes("/projects/vanguard/integration")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        website_status: { code: "NOT_CONFIGURED", label_ru: "Не настроено", ui_state: "NO DATA" },
        integration_status: { code: "CONNECTED", label_ru: "Подключено", ui_state: "ONLINE" },
        diagnostics: {
          website: { code: "NOT_CONFIGURED", ui_state: "NO DATA" },
          integration: { code: "CONNECTED", ui_state: "ONLINE" },
        },
        website: { name: "Vanguard", public_url: null, site_path: "/vanguard" },
        stages: [],
      }),
    };
  }
  if (u.includes("/projects/vanguard")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        project: { project_key: "vanguard", name: "Vanguard" },
        cards: {},
        attribution: { first_touch: { source: "meta" }, last_touch: { source: "google" }, utm: {} },
        source_analytics: { items: [{ source: "meta", leads: 1, candidates: 0 }] },
        marketing: { campaigns: [{ name: "Meta Launch", source: "meta", leads: 1, cpl: null }] },
        funnel: { steps: [{ id: "lead", label_ru: "Лид", count: 1 }] },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount(path: string) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/recruiting/projects/:projectKey" element={<VanguardProjectPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint Recruiting 1.5 ads control center", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("shows Russian campaign form and provider names", async () => {
    mount("/workspace/recruiting/projects/vanguard?tab=campaigns");
    expect(await screen.findByTestId("vanguard-campaigns")).toBeTruthy();
    expect(screen.getByTestId("vanguard-campaign-form")).toBeTruthy();
    expect(screen.getByTestId("vanguard-campaigns").textContent).toMatch(/Meta Ads/);
    expect(screen.getByTestId("vanguard-campaigns").textContent).toMatch(/Google Ads/);
    expect(screen.getByTestId("vanguard-campaigns").textContent).toMatch(/TikTok Ads/);
    expect(screen.getByTestId("vanguard-campaigns").textContent).toMatch(/Провайдер не подключен/);
    fireEvent.change(screen.getByPlaceholderText("Название"), { target: { value: "Meta Launch" } });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить кампанию" }));
  });

  it("shows Russian attribution labels", async () => {
    mount("/workspace/recruiting/projects/vanguard?tab=attribution");
    expect(await screen.findByTestId("vanguard-attribution")).toBeTruthy();
    expect(screen.getByTestId("vanguard-attribution").textContent).toMatch(/Первый контакт/);
    expect(screen.getByTestId("vanguard-attribution").textContent).toMatch(/Последний контакт/);
    expect(screen.getByTestId("vanguard-attribution").textContent).not.toMatch(/Website name/);
  });
});
