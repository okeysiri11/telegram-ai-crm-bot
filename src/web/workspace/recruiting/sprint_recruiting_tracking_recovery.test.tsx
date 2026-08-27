/**
 * Tracking recovery counters on the infrastructure page.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RecruitingInfraPage } from "./RecruitingInfraPage";

vi.stubGlobal(
  "fetch",
  vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      ok: true,
      components: {
        postgresql: { code: "CONNECTED", label_ru: "Работает" },
        redis: { code: "CONNECTED", label_ru: "Работает" },
        tracking_worker: { code: "CONNECTED", label_ru: "Работает" },
        meta_ads: { code: "NOT_CONFIGURED", label_ru: "Не настроено" },
      },
      tracking: {
        pending: 0,
        processing: 0,
        retrying: 0,
        waiting_provider: 4,
        delivered: 270,
        dead_letter: 0,
        provider_not_configured: 4,
      },
    }),
  })),
);

describe("Recruiting tracking recovery counters", () => {
  beforeEach(() => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockClear();
  });

  it("exposes waiting_provider and dead_letter without mapping NOT_CONFIGURED to error", async () => {
    render(
      <MemoryRouter initialEntries={["/workspace/recruiting/infra?embed=1"]}>
        <Routes>
          <Route path="/workspace/recruiting/infra" element={<RecruitingInfraPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("recruiting-infra-page")).toBeTruthy();
    const counts = screen.getByTestId("infra-tracking-counts").textContent || "";
    expect(counts).toContain("waiting_provider");
    expect(counts).toContain("dead_letter");
    expect(counts).toContain("4");
    expect(screen.getByTestId("infra-row-meta_ads").textContent).not.toContain("Ошибка");
  });
});
