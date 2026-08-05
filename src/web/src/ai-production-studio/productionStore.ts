/**
 * AI Production / AI Studio store — Sprint 27.9 → 28.3.
 * Client orchestration over creative catalogs + projects.
 * Execution: productionRuntime / Job Manager only.
 */

import { create } from "zustand";
import { productionRuntime } from "@/enterprise-runtime/productionRuntime";
import { universalPipelineForStudio } from "@/enterprise-runtime/universalPipelines";
import { aiAgentRuntime } from "@/enterprise-runtime/aiAgentRuntime";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { agentOs } from "@/enterprise-runtime/agentOs";
import {
  PRODUCTION_SESSION_KEY,
  nextStage,
  prevStage,
  resolvePromptVariables,
  seedGenerations,
  seedJobs,
  seedMedia,
  seedPipelines,
  seedProjects,
  seedPromptCollections,
  seedPrompts,
  studioById,
  type AutomationJob,
  type CreativePrompt,
  type GenerationRecord,
  type MediaAsset,
  type MediaKind,
  type PipelineStageId,
  type ProductionPipeline,
  type ProductionStudioId,
  type PromptCollection,
  type StudioProject,
} from "./productionCatalog";
import { brandVariables, readBrandKit, writeBrandKit, type BrandKit } from "./brandKit";
import { estimateGenerationMeter } from "./productionAnalytics";
import { launchN8nWorkflow } from "@/enterprise-integrations/n8nBridge";

export type ProductionView =
  | "home"
  | "studio"
  | "pipeline"
  | "prompts"
  | "media"
  | "automation"
  | "runtime"
  | "projects"
  | "templates"
  | "assets"
  | "history"
  | "favorites"
  | "gallery"
  | "brand"
  | "queue";

type SnapshotV2 = {
  version: 2;
  activeStudioId: ProductionStudioId | null;
  activeProjectId: string | null;
  view: ProductionView;
  pipelines: ProductionPipeline[];
  prompts: CreativePrompt[];
  media: MediaAsset[];
  jobs: AutomationJob[];
  projects: StudioProject[];
  generations: GenerationRecord[];
  promptCollections: PromptCollection[];
  promptCategory: string | "all";
  promptQuery: string;
  mediaFilter: MediaKind | "all";
  updatedAt: string;
};

type SnapshotLegacy = {
  version: 1;
  activeStudioId: ProductionStudioId | null;
  view: ProductionView;
  pipelines: ProductionPipeline[];
  prompts: CreativePrompt[];
  media: MediaAsset[];
  jobs: AutomationJob[];
  promptQuery: string;
  mediaFilter: MediaKind | "all";
  updatedAt: string;
};

type ProductionState = SnapshotV2 & {
  hydrated: boolean;
  hydrate: () => void;
  persist: () => void;
  setView: (view: ProductionView) => void;
  openStudio: (id: ProductionStudioId) => void;
  createPipeline: (title: string, studioId: ProductionStudioId, agents: string[]) => string;
  advancePipeline: (id: string) => void;
  retreatPipeline: (id: string) => void;
  setPipelineStage: (id: string, stage: PipelineStageId) => void;
  setAgentChain: (id: string, agents: string[]) => void;
  attachPrompt: (pipelineId: string, promptId: string) => void;
  togglePromptFavorite: (id: string) => void;
  bumpPromptVersion: (id: string, body: string) => void;
  setPromptQuery: (q: string) => void;
  setPromptCategory: (c: string | "all") => void;
  setMediaFilter: (f: MediaKind | "all") => void;
  addMedia: (partial: Omit<MediaAsset, "id" | "updatedAt" | "version">) => string;
  enqueueJob: (partial: Omit<AutomationJob, "id" | "updatedAt" | "retries" | "status">) => string;
  retryJob: (id: string) => void;
  runUniversalPipeline: (studioId: ProductionStudioId, title?: string) => string[];
  filteredPrompts: () => CreativePrompt[];
  filteredMedia: () => MediaAsset[];
  // Sprint 28.3
  openProject: (id: string) => void;
  createProject: (title: string, studioId: ProductionStudioId, description?: string) => string;
  toggleProjectFavorite: (id: string) => void;
  recentProjects: () => StudioProject[];
  favoriteProjects: () => StudioProject[];
  favoritePrompts: () => CreativePrompt[];
  favoriteGenerations: () => GenerationRecord[];
  generateInStudio: (
    studioId: ProductionStudioId,
    opts?: {
      projectId?: string;
      promptId?: string;
      variables?: Record<string, string>;
      multiAgent?: boolean;
      title?: string;
      providerId?: string;
      viaN8n?: boolean;
    },
  ) => string;
  settleGeneration: (id: string, status?: "done" | "failed") => void;
  brandKit: () => BrandKit;
  updateBrandKit: (partial: Partial<BrandKit>) => BrandKit;
  recommendAgents: (studioId: ProductionStudioId) => string[];
  suggestPrompts: (studioId: ProductionStudioId) => CreativePrompt[];
  projectDashboard: (projectId: string) => {
    project: StudioProject | null;
    pipelines: ProductionPipeline[];
    media: MediaAsset[];
    generations: GenerationRecord[];
    queueDepth: number;
    etaSec: number;
  };
};

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

function migrate(raw: SnapshotLegacy | SnapshotV2): SnapshotV2 {
  if (raw.version === 2) return raw;
  return {
    version: 2,
    activeStudioId: raw.activeStudioId,
    activeProjectId: null,
    view: raw.view === "home" ? "home" : raw.view,
    pipelines: raw.pipelines,
    prompts: raw.prompts,
    media: raw.media,
    jobs: raw.jobs,
    projects: seedProjects(),
    generations: seedGenerations(),
    promptCollections: seedPromptCollections(),
    promptCategory: "all",
    promptQuery: "",
    mediaFilter: raw.mediaFilter || "all",
    updatedAt: raw.updatedAt || new Date().toISOString(),
  };
}

function readSnap(): SnapshotV2 | null {
  try {
    const raw = localStorage.getItem(PRODUCTION_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SnapshotLegacy | SnapshotV2;
    if (parsed.version !== 1 && parsed.version !== 2) return null;
    return migrate(parsed);
  } catch {
    return null;
  }
}

export const useProductionStore = create<ProductionState>((set, get) => ({
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
  updatedAt: new Date().toISOString(),

  hydrate: () => {
    if (get().hydrated) return;
    const snap = typeof window !== "undefined" ? readSnap() : null;
    if (snap) {
      set({
        ...snap,
        hydrated: true,
        promptQuery: "",
        promptCategory: snap.promptCategory || "all",
        mediaFilter: snap.mediaFilter || "all",
        projects: snap.projects?.length ? snap.projects : seedProjects(),
        generations: snap.generations?.length ? snap.generations : seedGenerations(),
        promptCollections: snap.promptCollections?.length
          ? snap.promptCollections
          : seedPromptCollections(),
      });
      return;
    }
    set({
      hydrated: true,
      version: 2,
      pipelines: seedPipelines(),
      prompts: seedPrompts(),
      media: seedMedia(),
      jobs: seedJobs(),
      projects: seedProjects(),
      generations: seedGenerations(),
      promptCollections: seedPromptCollections(),
    });
    get().persist();
  },

  persist: () => {
    const s = get();
    const snap: SnapshotV2 = {
      version: 2,
      activeStudioId: s.activeStudioId,
      activeProjectId: s.activeProjectId,
      view: s.view,
      pipelines: s.pipelines,
      prompts: s.prompts,
      media: s.media,
      jobs: s.jobs,
      projects: s.projects,
      generations: s.generations,
      promptCollections: s.promptCollections,
      promptCategory: s.promptCategory,
      promptQuery: "",
      mediaFilter: s.mediaFilter,
      updatedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(PRODUCTION_SESSION_KEY, JSON.stringify(snap));
    } catch {
      /* ignore */
    }
  },

  setView: (view) => {
    if (get().view === view) return;
    set({ view });
    get().persist();
  },

  openStudio: (id) => {
    if (get().activeStudioId === id && get().view === "studio") return;
    set({ activeStudioId: id, view: "studio" });
    get().persist();
  },

  createPipeline: (title, studioId, agents) => {
    const id = uid("pp");
    const pipe: ProductionPipeline = {
      id,
      title,
      studioId,
      stage: "draft",
      agentChain: agents,
      mediaIds: [],
      updatedAt: new Date().toISOString(),
    };
    set((s) => ({ pipelines: [pipe, ...s.pipelines], view: "pipeline" }));
    get().persist();
    return id;
  },

  advancePipeline: (id) => {
    set((s) => ({
      pipelines: s.pipelines.map((p) => {
        if (p.id !== id) return p;
        const n = nextStage(p.stage);
        return n ? { ...p, stage: n, updatedAt: new Date().toISOString() } : p;
      }),
    }));
    get().persist();
  },

  retreatPipeline: (id) => {
    set((s) => ({
      pipelines: s.pipelines.map((p) => {
        if (p.id !== id) return p;
        const n = prevStage(p.stage);
        return n ? { ...p, stage: n, updatedAt: new Date().toISOString() } : p;
      }),
    }));
    get().persist();
  },

  setPipelineStage: (id, stage) => {
    set((s) => ({
      pipelines: s.pipelines.map((p) =>
        p.id === id ? { ...p, stage, updatedAt: new Date().toISOString() } : p,
      ),
    }));
    get().persist();
  },

  setAgentChain: (id, agents) => {
    set((s) => ({
      pipelines: s.pipelines.map((p) =>
        p.id === id ? { ...p, agentChain: agents, updatedAt: new Date().toISOString() } : p,
      ),
    }));
    get().persist();
  },

  attachPrompt: (pipelineId, promptId) => {
    set((s) => ({
      pipelines: s.pipelines.map((p) =>
        p.id === pipelineId ? { ...p, promptId, updatedAt: new Date().toISOString() } : p,
      ),
    }));
    get().persist();
  },

  togglePromptFavorite: (id) => {
    set((s) => ({
      prompts: s.prompts.map((p) => (p.id === id ? { ...p, favorite: !p.favorite } : p)),
    }));
    get().persist();
  },

  bumpPromptVersion: (id, body) => {
    const now = new Date().toISOString();
    set((s) => ({
      prompts: s.prompts.map((p) => {
        if (p.id !== id) return p;
        const version = p.version + 1;
        return {
          ...p,
          body,
          version,
          updatedAt: now,
          history: [{ version, body, at: now }, ...p.history].slice(0, 20),
        };
      }),
    }));
    get().persist();
  },

  setPromptQuery: (q) => set({ promptQuery: q }),

  setPromptCategory: (c) => {
    set({ promptCategory: c });
    get().persist();
  },

  setMediaFilter: (f) => {
    set({ mediaFilter: f });
    get().persist();
  },

  addMedia: (partial) => {
    const id = uid("ma");
    const asset: MediaAsset = {
      ...partial,
      id,
      version: 1,
      updatedAt: new Date().toISOString(),
    };
    set((s) => ({ media: [asset, ...s.media] }));
    get().persist();
    return id;
  },

  enqueueJob: (partial) => {
    const id = uid("aj");
    const job: AutomationJob = {
      ...partial,
      id,
      status: "queued",
      retries: 0,
      updatedAt: new Date().toISOString(),
    };
    set((s) => ({ jobs: [job, ...s.jobs], view: "automation" }));
    get().persist();
    productionRuntime.enqueue({
      title: job.title,
      queueKind:
        job.kind === "schedule"
          ? "publishing"
          : job.title.toLowerCase().includes("render")
            ? "render"
            : job.kind === "batch"
              ? "task"
              : "production",
      pipelineId: job.pipelineId,
      studioId: get().activeStudioId || undefined,
    });
    return id;
  },

  retryJob: (id) => {
    set((s) => ({
      jobs: s.jobs.map((j) =>
        j.id === id
          ? { ...j, status: "queued", retries: j.retries + 1, updatedAt: new Date().toISOString() }
          : j,
      ),
    }));
    get().persist();
    productionRuntime.retryFailed(8);
  },

  runUniversalPipeline: (studioId, title) => {
    const def = universalPipelineForStudio(studioId);
    const studio = studioById(studioId);
    if (!def) {
      const pipeId = get().createPipeline(
        title || `Run · ${studio?.short || studioId}`,
        studioId,
        studio?.aiAgents || [],
      );
      const jobId = productionRuntime.enqueue({
        title: title || `Production · ${studioId}`,
        queueKind: "production",
        studioId,
        pipelineId: pipeId,
        agents: studio?.aiAgents,
      });
      set({ view: "runtime" });
      get().persist();
      return [jobId];
    }
    const pipeId = get().createPipeline(title || def.label, studioId, def.defaultAgents);
    const { jobIds } = productionRuntime.runUniversalPipeline(def.id, {
      title: title || def.label,
      pipelineRefId: pipeId,
      extraAgents: studio?.aiAgents,
    });
    set({ view: "runtime" });
    get().persist();
    return jobIds;
  },

  filteredPrompts: () => {
    const q = get().promptQuery.trim().toLowerCase();
    const cat = get().promptCategory;
    let list = get().prompts;
    if (cat !== "all") list = list.filter((p) => p.category === cat);
    if (!q) return list;
    return list.filter((p) =>
      `${p.title} ${p.category} ${p.tags.join(" ")} ${p.body}`.toLowerCase().includes(q),
    );
  },

  filteredMedia: () => {
    const f = get().mediaFilter;
    const list = get().media;
    if (f === "all") return list;
    return list.filter((m) => m.kind === f);
  },

  openProject: (id) => {
    set({ activeProjectId: id, view: "projects" });
    get().persist();
  },

  createProject: (title, studioId, description) => {
    const id = uid("sp");
    const now = new Date().toISOString();
    const project: StudioProject = {
      id,
      title,
      studioId,
      description: description || "",
      favorite: false,
      pipelineIds: [],
      mediaIds: [],
      status: "draft",
      updatedAt: now,
      createdAt: now,
    };
    set((s) => ({
      projects: [project, ...s.projects],
      activeProjectId: id,
      view: "projects",
    }));
    get().persist();
    return id;
  },

  toggleProjectFavorite: (id) => {
    set((s) => ({
      projects: s.projects.map((p) => (p.id === id ? { ...p, favorite: !p.favorite } : p)),
    }));
    get().persist();
  },

  recentProjects: () =>
    [...get().projects].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 8),

  favoriteProjects: () => get().projects.filter((p) => p.favorite),

  favoritePrompts: () => get().prompts.filter((p) => p.favorite),

  favoriteGenerations: () => get().generations.filter((g) => g.favorite),

  recommendAgents: (studioId) => {
    const studio = studioById(studioId);
    const base = studio?.aiAgents || [];
    const fromCatalog = DEFAULT_AGENTS.filter((d) => d.studioHints.includes(studioId)).map((d) => d.nameRu);
    const live = aiAgentRuntime
      .list()
      .filter((a) => a.status === "idle" || a.status === "busy")
      .map((a) => a.name);
    return [...new Set([...base, ...fromCatalog.slice(0, 3), ...live.slice(0, 3)])];
  },

  suggestPrompts: (studioId) => {
    const studio = studioById(studioId);
    const cat = studioId === "prompt" ? "general" : studioId;
    return get()
      .prompts.filter((p) => p.category === cat || p.category === studio?.id || p.favorite)
      .slice(0, 5);
  },

  generateInStudio: (studioId, opts) => {
    const started = Date.now();
    const now = new Date().toISOString();
    const studio = studioById(studioId);
    const kit = readBrandKit();
    const prompt = opts?.promptId
      ? get().prompts.find((p) => p.id === opts.promptId)
      : get().suggestPrompts(studioId)[0];
    const agents = opts?.multiAgent
      ? get().recommendAgents(studioId)
      : (studio?.aiAgents.slice(0, 1) || ["Concierge"]);
    const variables = { ...brandVariables(kit), ...(opts?.variables || {}) };
    const resolved = prompt
      ? resolvePromptVariables(prompt.body, variables)
      : `Generate ${studio?.label || studioId} content`;
    const title = opts?.title || `${studio?.short || studioId} · generation`;
    const providerId = opts?.providerId || kit.defaultProviders[0] || "openai";
    if (opts?.viaN8n) {
      launchN8nWorkflow("n8n_tpl_media_pipeline", `wf_${studioId}_${Date.now().toString(36)}`);
    }
    const jobIds = get().runUniversalPipeline(studioId, title);
    const meter = estimateGenerationMeter(providerId, resolved.length);
    const mediaId = get().addMedia({
      name: `${title} output`,
      kind:
        studioId === "video" || studioId === "reels"
          ? "video"
          : studioId === "audio" || studioId === "voice"
            ? "audio"
            : studioId === "templates"
              ? "template"
              : "image",
      studioId,
      tags: ["generated", studioId, providerId],
      status: "draft",
    });
    const genId = uid("gen");
    const record: GenerationRecord = {
      id: genId,
      projectId: opts?.projectId || get().activeProjectId,
      studioId,
      title,
      promptId: prompt?.id,
      resolvedPrompt: resolved,
      jobIds,
      mediaIds: [mediaId],
      agents,
      status: "running",
      favorite: false,
      createdAt: now,
      updatedAt: now,
      providerId,
      tokens: meter.tokens,
      costUsd: meter.costUsd,
      durationMs: 0,
      logs: [
        { at: now, message: `Queued via Runtime · provider ${providerId}`, level: "info" },
        { at: now, message: `Prompt firewall / APH route · ${meter.tokens} tok · $${meter.costUsd}`, level: "info" },
        ...(opts?.viaN8n
          ? [{ at: now, message: "n8n external orchestration launched (no business logic)", level: "info" as const }]
          : []),
      ],
    };
    set((s) => {
      const projects = opts?.projectId
        ? s.projects.map((p) =>
            p.id === opts.projectId
              ? {
                  ...p,
                  mediaIds: [mediaId, ...p.mediaIds],
                  updatedAt: now,
                  status: "active" as const,
                }
              : p,
          )
        : s.projects;
      return {
        generations: [record, ...s.generations].slice(0, 80),
        projects,
        view: "history",
        activeStudioId: studioId,
      };
    });
    get().persist();
    // AgentOS: production agent tracks the run
    agentOs.launch("agent_production", title);
    agentOs.remember({
      agentId: "agent_production",
      kind: "session",
      key: `gen:${genId}`,
      value: resolved.slice(0, 240),
      tenantId: "org_demo",
    });
    // Settle after Runtime workers pick up — client simulation of completion
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        get().settleGeneration(genId, "done");
        agentOs.complete("agent_production");
      }, 900);
    } else {
      get().settleGeneration(genId, "done");
      agentOs.complete("agent_production");
    }
    void started;
    return genId;
  },

  settleGeneration: (id, status = "done") => {
    const now = new Date().toISOString();
    set((s) => ({
      generations: s.generations.map((g) => {
        if (g.id !== id) return g;
        const durationMs = Math.max(200, Date.now() - Date.parse(g.createdAt));
        return {
          ...g,
          status,
          durationMs,
          updatedAt: now,
          logs: [
            ...(g.logs || []),
            {
              at: now,
              message: status === "done" ? "Completed via Enterprise Runtime" : "Failed",
              level: status === "done" ? ("info" as const) : ("error" as const),
            },
          ],
        };
      }),
      jobs: s.jobs.map((j) =>
        status === "done" && j.status === "running"
          ? { ...j, status: "done" as const, updatedAt: now }
          : j,
      ),
    }));
    get().persist();
  },

  brandKit: () => readBrandKit(),

  updateBrandKit: (partial) => {
    const next = writeBrandKit({ ...readBrandKit(), ...partial });
    get().persist();
    return next;
  },

  projectDashboard: (projectId) => {
    const project = get().projects.find((p) => p.id === projectId) || null;
    const pipelines = get().pipelines.filter((p) => project?.pipelineIds.includes(p.id));
    const media = get().media.filter((m) => project?.mediaIds.includes(m.id));
    const generations = get().generations.filter((g) => g.projectId === projectId);
    const mon = productionRuntime.monitor();
    const queueDepth =
      mon.queues.generation.length + mon.queues.render.length + mon.queues.task.length;
    return {
      project,
      pipelines,
      media,
      generations,
      queueDepth,
      etaSec: mon.analytics.estimatedClearSec,
    };
  },
}));
