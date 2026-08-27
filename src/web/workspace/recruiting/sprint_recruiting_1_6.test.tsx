/**
 * Sprint Recruiting 1.6 — infrastructure diagnostics UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RecruitingInfraPage } from "./RecruitingInfraPage";

const fetchMock = vi.fn(async (url: string) => {
  const u = String(url);
  if (u.includes("/ops/diagnostics")) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        components: {
          postgresql: { code: "CONNECTED", label_ru: "Работает", tone: "success" },
          redis: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          rate_limit_store: { code: "DEGRADED", label_ru: "Ограничено", tone: "warning", backend: "process_local", shared: false },
          replay_store: { code: "DEGRADED", label_ru: "Ограничено", tone: "warning", backend: "process_local", shared: false },
          tracking_worker: { code: "CONNECTED", label_ru: "Работает", tone: "success" },
          vanguard_integration: { code: "CONNECTED", label_ru: "Работает", tone: "success" },
          vanguard_website: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info", required_env: ["VANGUARD_WEBSITE_URL"] },
          meta_ads: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          google_ads: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          tiktok_ads: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          telegram: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          whatsapp: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          email: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          anti_bot: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
          ci_e2e: { code: "NOT_CONFIGURED", label_ru: "Не настроено", tone: "info" },
        },
        tracking: { delivered: 2, retrying: 0, failed: 0, pending: 0, processing: 0, waiting_provider: 1, dead_letter: 0, provider_not_configured: 1, oldest_pending: null, last_delivery: "2026-08-27" },
      }),
    };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
});

vi.stubGlobal("fetch", fetchMock);

function mount() {
  return render(
    <MemoryRouter initialEntries={["/workspace/recruiting/infra?embed=1"]}>
      <Routes>
        <Route path="/workspace/recruiting/infra" element={<RecruitingInfraPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint Recruiting 1.6 infrastructure page", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("shows Russian operational states and never maps NOT_CONFIGURED to Ошибка", async () => {
    mount();
    expect(await screen.findByTestId("recruiting-infra-page")).toBeTruthy();
    expect(screen.getByTestId("infra-row-meta_ads").textContent).toContain("Не настроено");
    expect(screen.getByTestId("infra-row-meta_ads").textContent).not.toContain("Ошибка");
    expect(screen.getByTestId("infra-row-vanguard_website").textContent).toContain("Не настроено");
    expect(screen.getByTestId("infra-row-vanguard_website").textContent).toContain("VANGUARD_WEBSITE_URL");
    expect(screen.getByTestId("infra-row-postgresql").textContent).toContain("Работает");
    expect(screen.getByTestId("infra-row-rate_limit_store").textContent).toContain("Ограничено");
    expect(screen.getByText("Meta Ads")).toBeTruthy();
    expect(screen.getByText("Google Ads")).toBeTruthy();
    expect(screen.getByText("TikTok Ads")).toBeTruthy();
    expect(screen.getByTestId("infra-tracking-counts").textContent).toContain("provider_not_configured");
    expect(screen.getByTestId("infra-tracking-counts").textContent).toContain("waiting_provider");
    expect(screen.getByTestId("infra-tracking-counts").textContent).toContain("dead_letter");
  });
});
