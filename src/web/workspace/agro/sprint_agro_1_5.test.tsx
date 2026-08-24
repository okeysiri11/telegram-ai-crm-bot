/**
 * AGRO 1.5 — analytics desk: run, history, sources, gaps.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";

const analysis = {
  id: "an-15",
  title_ru: "Оперативный анализ",
  analysis_type: "operational",
  topic_ru: "Общий рынок",
  bias: "WATCH",
  confidence: 67,
  generated_at_human: "17 августа, 14:12",
  sources_count: 7,
  specialists_executed: ["ukraine", "trade", "price", "chief"],
  chief: { bias: "WATCH", confidence: 67, note_ru: "Метаданные каталогов, не рыночные ряды." },
  key_factors: ["Митна статистика"],
  what_changed: [{ marker: "NEW", text: "новый источник: ua_customs_open_data" }],
  risks: [{ text: "Просроченные счета" }],
  opportunities: [],
  sections: {
    prices: { status: "INSUFFICIENT", note_ru: "Недостаточно данных", bullets: [] },
    trade: { status: "DATA", bullets: [{ text: "Митна статистика", metadata_only: true }] },
    weather: { status: "INSUFFICIENT", note_ru: "Недостаточно данных", bullets: [] },
    harvest: { status: "INSUFFICIENT", note_ru: "Недостаточно данных", bullets: [] },
    logistics: { status: "INSUFFICIENT", note_ru: "Недостаточно данных", bullets: [] },
    world: { status: "INSUFFICIENT", note_ru: "Недостаточно данных", bullets: [] },
  },
  consensus: [{ agent: "trade", label_ru: "Торговый агент", conclusion: "Митна статистика" }],
  sources: [{ provider_id: "ua_customs_open_data", label_ru: "Таможня", records: [{ id: "o1", text: "Митна статистика" }] }],
  data_gaps: ["Рыночные биржевые котировки не подключены."],
  freshness: [{ provider_id: "ua_customs_open_data", label_ru: "Таможня", age_ru: "6 часов" }],
};

vi.mock("../business-ops/opsApi", () => ({
  pick: (row: Record<string, unknown>, ...keys: string[]) => {
    for (const k of keys) {
      if (row && row[k] != null && String(row[k])) return String(row[k]);
    }
    return "";
  },
  agroOpsGet: vi.fn(async (path: string) => {
    if (path.includes("/analytics/dashboard")) {
      return { ok: true, status: 200, json: { freshness: analysis.freshness, gaps: analysis.data_gaps, observation_count: 1, providers_available: 2 } };
    }
    if (path === "/analytics" || path.endsWith("/analytics")) {
      return { ok: true, status: 200, json: { ok: true, items: [analysis] } };
    }
    if (path.includes("/analytics/an-15")) {
      return { ok: true, status: 200, json: { ok: true, item: analysis } };
    }
    return { ok: true, status: 200, json: { ok: true, items: [] } };
  }),
  agroOpsPost: vi.fn(async (path: string) => {
    if (path.includes("/analytics/run")) {
      return { ok: true, status: 201, json: { ok: true, item: { ...analysis, id: "an-15-new" } } };
    }
    return { ok: true, status: 201, json: { ok: true, item: { id: "created" } } };
  }),
}));

describe("AGRO 1.5 analytics", () => {
  it("shows freshness, gaps, and launches analysis", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    expect((await screen.findByTestId("agro-analytics-freshness")).textContent).toMatch(/Таможня/);
    expect(screen.getByTestId("agro-analytics-gaps").textContent).toMatch(/котировки/);
    fireEvent.click(screen.getByText("ЗАПУСТИТЬ АНАЛИЗ"));
    expect(await screen.findByTestId("agro-analytics-chief")).toBeTruthy();
    expect(screen.getByTestId("agro-analytics-chief").textContent).toMatch(/WATCH|Наблюдение|Следить/i);
  });

  it("opens stored analysis from history and shows sources", async () => {
    render(<AgroAnalyticsPanel headers={{}} canIntel />);
    const hist = await screen.findByTestId("agro-analytics-history");
    expect(hist.textContent).toMatch(/Оперативный/);
    fireEvent.click(screen.getAllByText("Открыть")[0]);
    fireEvent.click(await screen.findByText("Показать источники"));
    expect((await screen.findByTestId("agro-analytics-source-records")).textContent).toMatch(/Митна статистика/);
  });
});
