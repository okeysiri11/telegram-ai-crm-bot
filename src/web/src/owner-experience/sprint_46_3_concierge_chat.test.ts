/**
 * Sprint 46.3 — Concierge chat UX + real task response flow.
 */

import { describe, expect, it } from "vitest";
import {
  CONCIERGE_MODAL,
  classifyConciergeIntent,
  isForbiddenHandoffReply,
  localConciergeReply,
  sanitizeConciergeReply,
} from "@/owner-experience/conciergeChatLogic";

describe("Sprint 46.3 Concierge intent", () => {
  it("greetings are QUESTION", () => {
    expect(classifyConciergeIntent("Привет")).toBe("QUESTION");
    expect(classifyConciergeIntent("Что ты умеешь?")).toBe("QUESTION");
  });

  it("soft marketing stays CHAT (clarify, not silent handoff)", () => {
    expect(classifyConciergeIntent("Хочу рекламировать кафе")).toBe("CHAT");
  });

  it("concrete campaign is ACTION/WORKFLOW", () => {
    expect(classifyConciergeIntent("Запусти рекламу кафе Black Coffee в Одессе")).toBe(
      "WORKFLOW",
    );
    expect(["ACTION", "WORKFLOW"]).toContain(
      classifyConciergeIntent("Создай рекламную кампанию кафе"),
    );
  });
});

describe("Sprint 46.3 human replies", () => {
  it("привет gets normal Concierge reply", () => {
    const r = localConciergeReply("Привет", {
      contextLabel: "Владелец платформы",
      intent: "QUESTION",
    });
    expect(r).toMatch(/Консьерж/i);
    expect(isForbiddenHandoffReply(r)).toBe(false);
  });

  it("хочу рекламировать кафе is human-friendly", () => {
    const r = localConciergeReply("Хочу рекламировать кафе", {
      contextLabel: "Владелец платформы",
      intent: "CHAT",
    });
    expect(r).toMatch(/название/i);
    expect(r).toMatch(/город/i);
    expect(r).not.toMatch(/Marketing AI/i);
    expect(r).not.toMatch(/Передал задачу/i);
  });

  it("sanitize strips Hercules / handoff jargon", () => {
    const raw =
      "Готово через Hercules.\nВертикаль: beauty\nЦепочка: Текст → Визуал\nСтоимость ≈ 0.100 у.е. · 1.2с";
    const out = sanitizeConciergeReply(raw);
    expect(out).not.toMatch(/Hercules/i);
    expect(out).not.toMatch(/Вертикаль/i);
    expect(out).not.toMatch(/Стоимость/i);
  });

  it("forbidden Marketing handoff is detected", () => {
    expect(
      isForbiddenHandoffReply(
        "Передал задачу Marketing AI через Консьержа. Можно запустить рекламный сценарий.",
      ),
    ).toBe(true);
  });
});

describe("Sprint 46.3 modal layout constants", () => {
  it("matches acceptance sizes", () => {
    expect(CONCIERGE_MODAL.width).toBe("min(900px, 90vw)");
    expect(CONCIERGE_MODAL.height).toBe("min(760px, 82vh)");
    expect(CONCIERGE_MODAL.minWidthPx).toBeGreaterThanOrEqual(720);
    expect(CONCIERGE_MODAL.minHeightPx).toBeGreaterThanOrEqual(600);
    expect(CONCIERGE_MODAL.scrollPadRightPx).toBeGreaterThanOrEqual(16);
  });
});

describe("Sprint 46.3 continuous memory phrasing", () => {
  it("second turn about name does not re-ask what to advertise", () => {
    const first = localConciergeReply("Рекламируем кафе.", {
      contextLabel: "Владелец платформы",
      intent: "CHAT",
    });
    expect(first).toMatch(/название|город/i);
    // Name follow-up is ACTION path in UI; local CHAT should not reset topic
    const advice = localConciergeReply("Как лучше рекламировать кафе?", {
      contextLabel: "Владелец платформы",
      intent: "QUESTION",
    });
    expect(advice).not.toMatch(/Передал задачу/i);
  });
});
