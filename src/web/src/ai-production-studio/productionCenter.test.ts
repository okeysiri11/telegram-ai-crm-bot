import { beforeEach, describe, expect, it } from "vitest";
import {
  PIPELINE_STAGES,
  PRODUCTION_SESSION_KEY,
  PRODUCTION_STUDIOS,
  nextStage,
  prevStage,
  seedPrompts,
} from "./productionCatalog";
import { useProductionStore } from "./productionStore";

describe("Sprint 27.9 AI Production Center", () => {
  beforeEach(() => {
    localStorage.removeItem(PRODUCTION_SESSION_KEY);
    useProductionStore.setState({
      hydrated: false,
      version: 2,
      activeStudioId: null,
      activeProjectId: null,
      view: "home",
      pipelines: [],
      prompts: [],
      media: [],
      jobs: [],
      projects: [],
      generations: [],
      promptCollections: [],
      promptCategory: "all",
      promptQuery: "",
      mediaFilter: "all",
    });
  });

  it("exposes production studios including presentation and social", () => {
    expect(PRODUCTION_STUDIOS.length).toBeGreaterThanOrEqual(20);
    expect(PRODUCTION_STUDIOS.map((s) => s.id)).toEqual(
      expect.arrayContaining([
        "image",
        "video",
        "audio",
        "voice",
        "avatar",
        "reels",
        "ads",
        "creative",
        "prompt",
        "brand",
        "assets",
        "templates",
        "media",
        "render",
        "publishing",
        "scheduler",
        "analytics",
        "presentation",
        "tiktok",
        "instagram",
        "youtube",
      ]),
    );
    expect(PRODUCTION_STUDIOS.every((s) => s.aiAgents.length > 0)).toBe(true);
  });

  it("advances pipeline Draft through Archive", () => {
    expect(PIPELINE_STAGES).toHaveLength(7);
    expect(nextStage("draft")).toBe("review");
    expect(nextStage("publish")).toBe("archive");
    expect(nextStage("archive")).toBeNull();
    expect(prevStage("review")).toBe("draft");
    const store = useProductionStore.getState();
    store.hydrate();
    const id = store.createPipeline("Test", "reels", ["Reels Agent"]);
    expect(useProductionStore.getState().pipelines[0]!.stage).toBe("draft");
    store.advancePipeline(id);
    expect(useProductionStore.getState().pipelines.find((p) => p.id === id)!.stage).toBe("review");
  });

  it("supports prompt library search favorites and versions", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    expect(seedPrompts().length).toBeGreaterThanOrEqual(3);
    store.setPromptQuery("reels");
    expect(store.filteredPrompts().some((p) => p.id === "cp_reels_hook")).toBe(true);
    store.togglePromptFavorite("cp_ad_variant");
    expect(useProductionStore.getState().prompts.find((p) => p.id === "cp_ad_variant")!.favorite).toBe(true);
    const before = useProductionStore.getState().prompts.find((p) => p.id === "cp_reels_hook")!.version;
    store.bumpPromptVersion("cp_reels_hook", "updated body {{product}}");
    const after = useProductionStore.getState().prompts.find((p) => p.id === "cp_reels_hook")!;
    expect(after.version).toBe(before + 1);
    expect(after.history[0]!.body).toContain("updated body");
  });

  it("filters media and enqueues automation with retry", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    store.setMediaFilter("video");
    expect(store.filteredMedia().every((m) => m.kind === "video")).toBe(true);
    const jobId = store.enqueueJob({ title: "Batch", kind: "batch", notify: true });
    store.retryJob(jobId);
    expect(useProductionStore.getState().jobs.find((j) => j.id === jobId)!.retries).toBe(1);
    expect(localStorage.getItem(PRODUCTION_SESSION_KEY)).toBeTruthy();
  });

  it("runs universal pipeline through Production Runtime", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    const ids = store.runUniversalPipeline("reels", "Test reels run");
    expect(ids.length).toBeGreaterThan(0);
    expect(useProductionStore.getState().view).toBe("runtime");
    expect(useProductionStore.getState().pipelines.some((p) => p.studioId === "reels")).toBe(true);
  });
});
