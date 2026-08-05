/**
 * Sprint 28.3 — Enterprise AI Studio tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  AI_STUDIO_CORE_IDS,
  AI_STUDIO_VERSION,
  PRODUCTION_SESSION_KEY,
  resolvePromptVariables,
  seedPromptCollections,
} from "@/ai-production-studio/productionCatalog";
import { useProductionStore } from "@/ai-production-studio/productionStore";

describe("Sprint 28.3 Enterprise AI Studio", () => {
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

  it("exposes AI Studio version and core studios", () => {
    expect(AI_STUDIO_VERSION).toBe("32.0");
    expect(AI_STUDIO_CORE_IDS).toEqual(["image", "video", "audio", "voice", "avatar", "prompt"]);
  });

  it("resolves prompt variables", () => {
    expect(resolvePromptVariables("Hello {{name}}", { name: "ADOS" })).toBe("Hello ADOS");
  });

  it("seeds prompt collections", () => {
    expect(seedPromptCollections().length).toBeGreaterThanOrEqual(3);
  });

  it("creates projects and recent/favorites lists", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    const id = store.createProject("Demo", "image", "Hero stills");
    expect(useProductionStore.getState().projects.some((p) => p.id === id)).toBe(true);
    store.toggleProjectFavorite(id);
    expect(store.favoriteProjects().some((p) => p.id === id)).toBe(true);
    expect(store.recentProjects()[0]?.id).toBe(id);
  });

  it("filters prompts by category and search", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    store.setPromptCategory("image");
    expect(store.filteredPrompts().every((p) => p.category === "image")).toBe(true);
    store.setPromptCategory("all");
    store.setPromptQuery("hero");
    expect(store.filteredPrompts().some((p) => p.id === "cp_image_hero")).toBe(true);
  });

  it("generates via runtime and records history", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    const projectId = store.createProject("Gen proj", "reels");
    const genId = store.generateInStudio("reels", {
      projectId,
      multiAgent: true,
      variables: { product: "ADOS", audience: "exec", tone: "bold" },
    });
    const gen = useProductionStore.getState().generations.find((g) => g.id === genId);
    expect(gen).toBeTruthy();
    expect(gen!.jobIds.length).toBeGreaterThan(0);
    expect(gen!.mediaIds.length).toBeGreaterThan(0);
    expect(store.projectDashboard(projectId).media.length).toBeGreaterThan(0);
  });

  it("recommends agents and suggests prompts", () => {
    const store = useProductionStore.getState();
    store.hydrate();
    expect(store.recommendAgents("image").length).toBeGreaterThan(0);
    expect(store.suggestPrompts("image").length).toBeGreaterThan(0);
  });

  it("migrates v1 snapshot to v2 on hydrate", () => {
    localStorage.setItem(
      PRODUCTION_SESSION_KEY,
      JSON.stringify({
        version: 1,
        activeStudioId: null,
        view: "home",
        pipelines: [],
        prompts: [],
        media: [],
        jobs: [],
        promptQuery: "",
        mediaFilter: "all",
        updatedAt: new Date().toISOString(),
      }),
    );
    const store = useProductionStore.getState();
    store.hydrate();
    expect(useProductionStore.getState().version).toBe(2);
    expect(useProductionStore.getState().projects.length).toBeGreaterThan(0);
    expect(useProductionStore.getState().promptCollections.length).toBeGreaterThan(0);
  });
});
