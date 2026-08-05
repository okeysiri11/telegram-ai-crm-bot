/**
 * Sprint 32.0 — AI Production Studio Enterprise MVP tests.
 * Naming note: Enterprise Web Completion also uses Sprint 32.0.
 */
import { beforeEach, describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import { CONTENT_TYPES, PRODUCTION_HOME_NAV } from "@/ai-production-studio/contentTypes";
import { DEFAULT_BRAND_KIT, brandVariables, writeBrandKit } from "@/ai-production-studio/brandKit";
import { deriveProductionOwnerStats, estimateGenerationMeter } from "@/ai-production-studio/productionAnalytics";
import { useProductionStore } from "@/ai-production-studio/productionStore";
import { PRODUCTION_CENTER_VERSION } from "@/ai-production-studio/productionCatalog";
import { jobManager } from "@/enterprise-runtime/jobManager";

describe("Sprint 32.0 AI Production Studio MVP", () => {
  beforeEach(() => {
    localStorage.clear();
    useProductionStore.setState({
      hydrated: false,
      pipelines: [],
      prompts: [],
      media: [],
      jobs: [],
      projects: [],
      generations: [],
      promptCollections: [],
    });
  });

  it("bumps production center version and web sprint", () => {
    expect(PRODUCTION_CENTER_VERSION).toBe("32.0");
    expect(Number.parseFloat(webConfig.sprint)).toBeGreaterThanOrEqual(32.0);
  });

  it("exposes production home nav and content types", () => {
    expect(PRODUCTION_HOME_NAV.length).toBeGreaterThanOrEqual(10);
    expect(CONTENT_TYPES.map((c) => c.id)).toEqual(
      expect.arrayContaining(["text", "images", "video", "reels", "ads", "presentations", "pdf"]),
    );
  });

  it("brand kit injects variables and persists", () => {
    const kit = writeBrandKit({ ...DEFAULT_BRAND_KIT, name: "Demo Brand" });
    expect(kit.name).toBe("Demo Brand");
    const vars = brandVariables(kit);
    expect(vars.brand).toBe("Demo Brand");
    expect(vars.colors).toContain(kit.primaryColor);
  });

  it("generateInStudio enqueues Runtime jobs with cost and settles", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    const beforeJobs = jobManager.list().length;
    const genId = store.generateInStudio("image", {
      multiAgent: true,
      providerId: "openai",
      title: "MVP image run",
    });
    const gen = useProductionStore.getState().generations.find((g) => g.id === genId);
    expect(gen).toBeTruthy();
    expect(gen?.providerId).toBe("openai");
    expect(gen?.tokens).toBeGreaterThan(0);
    expect(gen?.costUsd).toBeGreaterThan(0);
    expect(gen?.jobIds.length).toBeGreaterThan(0);
    expect(jobManager.list().length).toBeGreaterThan(beforeJobs);
    store.settleGeneration(genId!, "done");
    expect(useProductionStore.getState().generations.find((g) => g.id === genId)?.status).toBe("done");
  });

  it("owner stats derive from generations and queues", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    store.generateInStudio("reels", { providerId: "groq", viaN8n: true });
    store.settleGeneration(useProductionStore.getState().generations[0]!.id, "done");
    const s = useProductionStore.getState();
    const stats = deriveProductionOwnerStats({
      generations: s.generations,
      prompts: s.prompts,
      jobs: s.jobs,
      pipelines: s.pipelines,
    });
    expect(stats.totalGenerations).toBeGreaterThan(0);
    expect(stats.costTotalUsd).toBeGreaterThanOrEqual(0);
    expect(stats.brand).toBeTruthy();
    expect(estimateGenerationMeter("openai", 300).tokens).toBeGreaterThan(200);
  });

  it("exports MVP panels", async () => {
    expect(typeof (await import("@/ai-production-studio/ProductionHomeDashboard")).ProductionHomeDashboard).toBe(
      "function",
    );
    expect(typeof (await import("@/ai-production-studio/WorkflowBuilderPanel")).WorkflowBuilderPanel).toBe(
      "function",
    );
    expect(typeof (await import("@/ai-production-studio/TaskQueuePanel")).TaskQueuePanel).toBe("function");
    expect(typeof (await import("@/ai-production-studio/BrandKitPanel")).BrandKitPanel).toBe("function");
  }, 20_000);
});
