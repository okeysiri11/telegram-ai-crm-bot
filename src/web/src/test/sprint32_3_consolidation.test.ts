import { describe, expect, it } from "vitest";
import {
  RUNTIME_LAYERS,
  canonicalRuntimeLayer,
  runtimeConsolidationSummary,
} from "../enterprise-runtime/runtimeConsolidation";

describe("Sprint 32.3 runtime consolidation", () => {
  it("enterprise runtime is the canonical web orchestration hub", () => {
    const hub = canonicalRuntimeLayer();
    expect(hub.id).toBe("enterprise");
    expect(hub.role).toBe("canonical");
    expect(hub.owns).toContain("jobManager");
    expect(RUNTIME_LAYERS.length).toBeGreaterThanOrEqual(5);
    const summary = runtimeConsolidationSummary();
    expect(summary.sprint).toBe("32.3");
    expect(summary.canonical).toContain("enterprise-runtime");
  });
});
