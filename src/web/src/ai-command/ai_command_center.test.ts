import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("AI Command Center page", () => {
  it("has RU tabs and chat surface", () => {
    const src = readFileSync(resolve(__dirname, "AiCommandCenterPage.tsx"), "utf-8");
    expect(src).toContain("AI Command Center");
    expect(src).toContain("ai-command-center");
    for (const t of ["Диалоги", "Агенты", "Инструменты", "История", "Голос", "Вертикали"]) {
      expect(src).toContain(t);
    }
  });
});
