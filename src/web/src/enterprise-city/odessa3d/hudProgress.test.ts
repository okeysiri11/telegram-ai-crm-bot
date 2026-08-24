import { describe, expect, it } from "vitest";
import { normalizeHudProgress } from "./hudProgress";

describe("normalizeHudProgress", () => {
  it("uses zeros when progress is undefined", () => {
    const hud = normalizeHudProgress(undefined);
    expect(hud.total).toBe(0);
    expect(hud.downloaded).toBe(0);
    expect(hud.parsed).toBe(0);
    expect(hud.active).toBe(0);
    expect(hud.boot).toBe("BOOTSTRAP");
    expect(hud.ready).toBe(false);
    expect(hud.failed).toBe(0);
    expect(hud.mb).toBe(0);
    expect(hud.fps).toBe(0);
    expect(hud.queued).toBe(0);
    expect(hud.loading).toBe(0);
  });

  it("keeps total at 0 for partial progress before the manifest count exists", () => {
    const hud = normalizeHudProgress({ loaded: 1, queued: 2, loading: 1, percent: 3 });
    expect(hud.total).toBe(0);
    expect(hud.loaded).toBe(1);
    expect(hud.queued).toBe(2);
  });

  it("takes total from loader/manifest state when it arrives (45)", () => {
    const hud = normalizeHudProgress({
      total: 45,
      activeCount: 1,
      downloadedCount: 2,
      parsedCount: 2,
      bootState: "INTERACTIVE",
      loadedMb: 3.2,
    });
    expect(hud.total).toBe(45);
    expect(hud.active).toBe(1);
    expect(hud.downloaded).toBe(2);
    expect(hud.parsed).toBe(2);
    expect(hud.boot).toBe("INTERACTIVE");
    expect(hud.mb).toBe(3.2);
    expect(hud.ready).toBe(false);
  });
});
