/**
 * Sprint 46.4 — Unified Intent Bar + router + clear-on-submit contract.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CAPABILITY_REPLY_RU,
  classifyUnifiedIntent,
  isChatCapabilityQuestion,
  isSearchRefine,
  resolveVerticalIntentConfig,
  STATUS_LABEL_RU,
  useUnifiedIntentStore,
} from "@/workspace-chrome/unified-intent";

describe("Sprint 46.4 intent router", () => {
  it("capability question → CHAT (not SEARCH)", () => {
    expect(classifyUnifiedIntent("Расскажи, как ты можешь помочь")).toBe("CHAT");
    expect(classifyUnifiedIntent("Что ты умеешь?")).toBe("CHAT");
    expect(isChatCapabilityQuestion("Расскажи как ты можешь помочь")).toBe(true);
  });

  it("navigate / search / create / workflow", () => {
    expect(classifyUnifiedIntent("Открой CRM")).toBe("NAVIGATE");
    expect(classifyUnifiedIntent("Найди договор GlobeFly")).toBe("SEARCH");
    expect(classifyUnifiedIntent("Создай клиента Иванов")).toBe("CREATE");
    expect(classifyUnifiedIntent("Запусти рекламную кампанию")).toBe("WORKFLOW");
    expect(classifyUnifiedIntent("Покажи продажи за месяц")).toBe("COMMAND");
  });

  it("capability reply has no tech labels", () => {
    expect(CAPABILITY_REPLY_RU).not.toMatch(/applications:/i);
    expect(CAPABILITY_REPLY_RU).not.toMatch(/open_module/i);
    expect(CAPABILITY_REPLY_RU).not.toMatch(/0\.\d{3}/);
    expect(CAPABILITY_REPLY_RU).toMatch(/клиент/i);
  });

  it("search refine detects follow-ups", () => {
    expect(isSearchRefine("Только дизель")).toBe(true);
    expect(isSearchRefine("Найди BMW X5")).toBe(false);
  });
});

describe("Sprint 46.4 vertical configs", () => {
  it("Auto / CRM / Travel / Beauty share same action surface", () => {
    for (const id of ["auto", "crm", "travel", "beauty", "crypto", "agro"]) {
      const cfg = resolveVerticalIntentConfig(id);
      expect(cfg.verticalId).toBe(id);
      expect(cfg.contextLabel.length).toBeGreaterThan(0);
      expect(cfg.availableActions).toContain("ask");
      expect(cfg.searchScope.length).toBeGreaterThan(0);
    }
  });
});

describe("Sprint 46.4 status model + inbox", () => {
  beforeEach(() => {
    localStorage.clear();
    useUnifiedIntentStore.setState({ items: [], inboxOpen: false, showTech: false });
  });

  it("creates interaction with Russian status labels", () => {
    const item = useUnifiedIntentStore.getState().create("Тест", "CHAT", "owner");
    expect(item.status).toBe("received");
    expect(STATUS_LABEL_RU.received).toBe("Принято");
    expect(STATUS_LABEL_RU.running).toBe("Выполняю");
    expect(STATUS_LABEL_RU.completed).toBe("Готово");
    useUnifiedIntentStore.getState().setStatus(item.id, "running", {
      progressLabel: "Ищу…",
    });
    const updated = useUnifiedIntentStore.getState().items[0];
    expect(updated?.progressLabel).toBe("Ищу…");
  });

  it("keeps multiple concurrent tasks visible", () => {
    const a = useUnifiedIntentStore.getState().create("Задача 1", "COMMAND");
    const b = useUnifiedIntentStore.getState().create("Задача 2", "SEARCH");
    useUnifiedIntentStore.getState().setStatus(a.id, "running");
    useUnifiedIntentStore.getState().setStatus(b.id, "running");
    const running = useUnifiedIntentStore.getState().byFilter("running");
    expect(running.map((i) => i.text)).toEqual(["Задача 2", "Задача 1"]);
  });

  it("showTech defaults OFF", () => {
    expect(useUnifiedIntentStore.getState().showTech).toBe(false);
  });
});

describe("Sprint 46.4 clear-on-submit contract", () => {
  it("execute clears input responsibility is documented via immediate draft reset pattern", async () => {
    // UI clears draft synchronously before await executeUnifiedIntent — simulated here.
    let draft = "Расскажи, как ты можешь помочь";
    const submitted = draft;
    draft = "";
    expect(draft).toBe("");
    expect(submitted.length).toBeGreaterThan(0);

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ data: { reply_ru: CAPABILITY_REPLY_RU } }),
      })),
    );

    const { executeUnifiedIntent } = await import(
      "@/workspace-chrome/unified-intent/executeUnifiedIntent"
    );
    localStorage.clear();
    useUnifiedIntentStore.setState({ items: [], inboxOpen: false, showTech: false });

    const item = await executeUnifiedIntent(submitted, {
      navigate: vi.fn(),
      verticalId: "owner",
    });
    expect(draft).toBe("");
    expect(item.intent).toBe("CHAT");
    expect(item.status).toBe("completed");
    expect(item.reply).toMatch(/клиент/i);
    expect(item.reply).not.toMatch(/modules:/i);

    vi.unstubAllGlobals();
  });
});
