import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Hercules Control Center", () => {
  it("exports page and defines RU tabs", () => {
    const src = readFileSync(
      resolve(__dirname, "HerculesControlCenterPage.tsx"),
      "utf-8",
    );
    expect(src).toContain("Hercules Control Center");
    for (const tab of ["Обзор", "Ресурсы", "GPU", "CPU", "Очереди", "Воркеры", "Метрики"]) {
      expect(src).toContain(tab);
    }
    expect(src).toContain("hercules-control-center");
  });
});
