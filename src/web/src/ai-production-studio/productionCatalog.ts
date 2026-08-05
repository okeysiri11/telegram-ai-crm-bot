/**
 * AI Production Center catalogs — Sprint 27.9.
 * Creative production surfaces only. Does NOT replace AI Builder prompts
 * or Platform Builder visual asset engines.
 */

export const PRODUCTION_SESSION_KEY = "ews_ai_production_v1";
export const PRODUCTION_CENTER_VERSION = "32.0";
export const AI_STUDIO_VERSION = "32.0";

/** Core visual studios for Enterprise AI Studio (Sprint 28.3). */
export const AI_STUDIO_CORE_IDS = [
  "image",
  "video",
  "audio",
  "voice",
  "avatar",
  "prompt",
] as const;

export type ProductionStudioId =
  | "image"
  | "video"
  | "audio"
  | "voice"
  | "avatar"
  | "reels"
  | "ads"
  | "creative"
  | "prompt"
  | "brand"
  | "assets"
  | "templates"
  | "media"
  | "render"
  | "publishing"
  | "scheduler"
  | "analytics"
  | "presentation"
  | "tiktok"
  | "instagram"
  | "youtube";

export type PipelineStageId =
  | "draft"
  | "review"
  | "approval"
  | "generation"
  | "render"
  | "publish"
  | "archive";

export type MediaKind =
  | "image"
  | "video"
  | "audio"
  | "document"
  | "template"
  | "brand"
  | "font"
  | "icon"
  | "animation";

export type ProductionStudioDef = {
  id: ProductionStudioId;
  label: string;
  labelRu?: string;
  short: string;
  group: "generate" | "brand" | "library" | "ops" | "social";
  description: string;
  /** Existing platform deep link when available */
  deepLink?: string;
  aiAgents: string[];
  cityBuildingId?: string;
};

export const PIPELINE_STAGES: { id: PipelineStageId; label: string; order: number }[] = [
  { id: "draft", label: "Draft", order: 0 },
  { id: "review", label: "Review", order: 1 },
  { id: "approval", label: "Approval", order: 2 },
  { id: "generation", label: "Generation", order: 3 },
  { id: "render", label: "Render", order: 4 },
  { id: "publish", label: "Publish", order: 5 },
  { id: "archive", label: "Archive", order: 6 },
];

/** 17 Production Center studios — City Production District destinations. */
export const PRODUCTION_STUDIOS: ProductionStudioDef[] = [
  {
    id: "image",
    label: "Image Studio",
    short: "Image",
    group: "generate",
    description: "Still images · variants · brand-safe crops",
    aiAgents: ["Creative Director", "Brand Compliance"],
    cityBuildingId: "prod_image",
  },
  {
    id: "video",
    label: "Video Studio",
    short: "Video",
    group: "generate",
    description: "Clips · timelines · scene boards",
    aiAgents: ["Video Director", "Editor Agent"],
    cityBuildingId: "prod_video",
  },
  {
    id: "audio",
    label: "Audio Studio",
    short: "Audio",
    group: "generate",
    description: "Beds · SFX · mix stems",
    aiAgents: ["Audio Agent"],
    cityBuildingId: "prod_audio",
  },
  {
    id: "voice",
    label: "Voice Studio",
    short: "Voice",
    group: "generate",
    description: "TTS · clone · localization",
    aiAgents: ["Voice Agent", "Localization"],
    cityBuildingId: "prod_voice",
  },
  {
    id: "avatar",
    label: "Avatar Studio",
    short: "Avatar",
    group: "generate",
    description: "Presenters · lip-sync · consent metadata",
    aiAgents: ["Avatar Agent", "Compliance"],
    cityBuildingId: "prod_avatar",
  },
  {
    id: "reels",
    label: "Reels Factory",
    short: "Reels",
    group: "generate",
    description: "9:16 social shorts pipeline",
    aiAgents: ["Reels Agent", "Hook Writer"],
    cityBuildingId: "prod_reels",
  },
  {
    id: "ads",
    label: "Ads Factory",
    short: "Ads",
    group: "generate",
    description: "Paid creative packs · A/B variants",
    aiAgents: ["Ads Agent", "Performance"],
    cityBuildingId: "prod_ads",
  },
  {
    id: "creative",
    label: "Creative Studio",
    short: "Creative",
    group: "generate",
    description: "Campaign briefs · multi-modal boards",
    aiAgents: ["Creative Director", "Concierge"],
    cityBuildingId: "prod_creative",
  },
  {
    id: "prompt",
    label: "Prompt Studio",
    short: "Prompts",
    group: "library",
    description: "Creative prompt library · versions · variables",
    aiAgents: ["Prompt Engineer"],
    cityBuildingId: "prod_prompt",
  },
  {
    id: "brand",
    label: "Brand Studio",
    short: "Brand",
    group: "brand",
    description: "Kits · tone · forbidden words · templates",
    deepLink: "/platform-builder/themes",
    aiAgents: ["Brand Compliance"],
    cityBuildingId: "prod_brand",
  },
  {
    id: "assets",
    label: "Asset Library",
    short: "Assets",
    group: "library",
    description: "Approved creative assets catalog",
    deepLink: "/platform-builder/assets",
    aiAgents: ["Asset Librarian"],
    cityBuildingId: "prod_assets",
  },
  {
    id: "templates",
    label: "Template Center",
    short: "Templates",
    group: "library",
    description: "Reusable creative templates",
    aiAgents: ["Template Agent"],
    cityBuildingId: "prod_templates",
  },
  {
    id: "media",
    label: "Media Storage",
    short: "Media",
    group: "library",
    description: "Unified media manager",
    deepLink: "/documents",
    aiAgents: ["Media Agent"],
    cityBuildingId: "prod_media",
  },
  {
    id: "render",
    label: "Render Center",
    short: "Render",
    group: "ops",
    description: "Queue · retries · farm status",
    deepLink: "/platform-builder/runtime",
    aiAgents: ["Render Orchestrator"],
    cityBuildingId: "prod_render",
  },
  {
    id: "publishing",
    label: "Publishing Center",
    short: "Publish",
    group: "ops",
    description: "Channels · approval gate · schedule",
    aiAgents: ["Publisher", "Compliance"],
    cityBuildingId: "prod_publish",
  },
  {
    id: "scheduler",
    label: "Scheduler",
    short: "Schedule",
    group: "ops",
    description: "Calendars · windows · batch slots",
    deepLink: "/automation",
    aiAgents: ["Scheduler Agent"],
    cityBuildingId: "prod_scheduler",
  },
  {
    id: "analytics",
    label: "Analytics Center",
    short: "Analytics",
    group: "ops",
    description: "Creative performance · reach",
    deepLink: "/analytics",
    aiAgents: ["Insights Agent"],
    cityBuildingId: "prod_analytics",
  },
  {
    id: "presentation",
    label: "Presentation Builder",
    labelRu: "Презентации",
    short: "Slides",
    group: "generate",
    description: "Slide decks · narrative boards · brand kits",
    aiAgents: ["Designer", "Copywriter", "Business Analyst"],
    cityBuildingId: "production",
  },
  {
    id: "tiktok",
    label: "TikTok",
    labelRu: "TikTok",
    short: "TikTok",
    group: "social",
    description: "Vertical publish pack · hooks · captions",
    aiAgents: ["Reels Agent", "Copywriter", "Marketing"],
    cityBuildingId: "prod_reels",
  },
  {
    id: "instagram",
    label: "Instagram",
    labelRu: "Instagram",
    short: "IG",
    group: "social",
    description: "Reels · carousels · stories publish",
    aiAgents: ["Reels Agent", "Designer", "Marketing"],
    cityBuildingId: "prod_reels",
  },
  {
    id: "youtube",
    label: "YouTube",
    labelRu: "YouTube",
    short: "YT",
    group: "social",
    description: "Long-form · shorts · thumbnails",
    aiAgents: ["Video Director", "Copywriter", "Marketing"],
    cityBuildingId: "prod_video",
  },
];

export const STUDIO_GROUPS = [
  { id: "generate", label: "Generation" },
  { id: "brand", label: "Brand" },
  { id: "library", label: "Library" },
  { id: "ops", label: "Operations" },
  { id: "social", label: "Social" },
] as const;

/** Sprint 30.5 — Russian Production UX quick actions */
export const PRODUCTION_QUICK_ACTIONS_RU: {
  id: string;
  label: string;
  studioId: ProductionStudioId;
}[] = [
  { id: "qa_image", label: "Создать изображение", studioId: "image" },
  { id: "qa_video", label: "Создать видео", studioId: "video" },
  { id: "qa_presentation", label: "Создать презентацию", studioId: "presentation" },
  { id: "qa_reel", label: "Создать Reel", studioId: "reels" },
  { id: "qa_doc", label: "Создать документ", studioId: "prompt" },
  { id: "qa_ads", label: "Создать рекламную кампанию", studioId: "ads" },
];

export type CreativePrompt = {
  id: string;
  title: string;
  category: string;
  body: string;
  tags: string[];
  variables: string[];
  version: number;
  favorite: boolean;
  updatedAt: string;
  history: { version: number; body: string; at: string }[];
};

export type MediaAsset = {
  id: string;
  name: string;
  kind: MediaKind;
  studioId: ProductionStudioId;
  tags: string[];
  version: number;
  status: "draft" | "approved" | "archived";
  updatedAt: string;
};

export type ProductionPipeline = {
  id: string;
  title: string;
  studioId: ProductionStudioId;
  stage: PipelineStageId;
  agentChain: string[];
  promptId?: string;
  mediaIds: string[];
  updatedAt: string;
};

export type AutomationJob = {
  id: string;
  title: string;
  kind: "batch" | "queue" | "schedule" | "retry";
  status: "queued" | "running" | "failed" | "done";
  retries: number;
  notify: boolean;
  scheduleAt?: string;
  pipelineId?: string;
  updatedAt: string;
};

/** Sprint 28.3 — Prompt collection grouping. */
export type PromptCollection = {
  id: string;
  title: string;
  category: string;
  promptIds: string[];
  description: string;
  updatedAt: string;
};

/** Sprint 28.3 — Studio project (orchestration over pipelines/media/jobs). */
export type StudioProject = {
  id: string;
  title: string;
  studioId: ProductionStudioId;
  description: string;
  favorite: boolean;
  pipelineIds: string[];
  mediaIds: string[];
  promptId?: string;
  status: "draft" | "active" | "completed" | "archived";
  updatedAt: string;
  createdAt: string;
};

/** Sprint 28.3 — Generation history record (links Runtime jobs → outputs). */
export type GenerationRecord = {
  id: string;
  projectId: string | null;
  studioId: ProductionStudioId;
  title: string;
  promptId?: string;
  resolvedPrompt?: string;
  jobIds: string[];
  mediaIds: string[];
  agents: string[];
  status: "queued" | "running" | "done" | "failed";
  favorite: boolean;
  createdAt: string;
  updatedAt: string;
  /** Sprint 32.0 — execution meter */
  providerId?: string;
  tokens?: number;
  costUsd?: number;
  durationMs?: number;
  logs?: { at: string; message: string; level?: "info" | "warn" | "error" }[];
};

export const PROMPT_CATEGORIES = [
  "reels",
  "ads",
  "brand",
  "voice",
  "image",
  "video",
  "audio",
  "avatar",
  "campaign",
  "general",
] as const;

export function resolvePromptVariables(
  body: string,
  values: Record<string, string>,
): string {
  return body.replace(/\{\{(\w+)\}\}/g, (_, key: string) => values[key] ?? `{{${key}}}`);
}

export function studioById(id: ProductionStudioId): ProductionStudioDef | undefined {
  return PRODUCTION_STUDIOS.find((s) => s.id === id);
}

export function nextStage(stage: PipelineStageId): PipelineStageId | null {
  const i = PIPELINE_STAGES.findIndex((s) => s.id === stage);
  if (i < 0 || i >= PIPELINE_STAGES.length - 1) return null;
  return PIPELINE_STAGES[i + 1]!.id;
}

export function prevStage(stage: PipelineStageId): PipelineStageId | null {
  const i = PIPELINE_STAGES.findIndex((s) => s.id === stage);
  if (i <= 0) return null;
  return PIPELINE_STAGES[i - 1]!.id;
}

export function seedPrompts(): CreativePrompt[] {
  const now = new Date().toISOString();
  return [
    {
      id: "cp_reels_hook",
      title: "Reels · Hook opener",
      category: "reels",
      body: "Create a 3-second hook for {{product}} targeting {{audience}} in brand tone {{tone}}.",
      tags: ["reels", "hook", "social"],
      variables: ["product", "audience", "tone"],
      version: 1,
      favorite: true,
      updatedAt: now,
      history: [{ version: 1, body: "Create a 3-second hook for {{product}} targeting {{audience}} in brand tone {{tone}}.", at: now }],
    },
    {
      id: "cp_ad_variant",
      title: "Ads · Variant pack",
      category: "ads",
      body: "Generate 3 ad copy variants for {{offer}} with CTA {{cta}}. Avoid: {{forbidden}}.",
      tags: ["ads", "copy", "ab"],
      variables: ["offer", "cta", "forbidden"],
      version: 1,
      favorite: false,
      updatedAt: now,
      history: [],
    },
    {
      id: "cp_brand_safe",
      title: "Brand · Safe image brief",
      category: "brand",
      body: "Describe a brand-safe image for {{campaign}} using palette {{colors}} and style {{style}}.",
      tags: ["brand", "image"],
      variables: ["campaign", "colors", "style"],
      version: 1,
      favorite: true,
      updatedAt: now,
      history: [],
    },
    {
      id: "cp_voice_script",
      title: "Voice · Narration script",
      category: "voice",
      body: "Write a {{duration}}s narration for {{topic}} in {{language}}.",
      tags: ["voice", "script"],
      variables: ["duration", "topic", "language"],
      version: 1,
      favorite: false,
      updatedAt: now,
      history: [],
    },
    {
      id: "cp_image_hero",
      title: "Image · Hero still",
      category: "image",
      body: "Generate a hero still for {{product}} in style {{style}} with lighting {{lighting}}.",
      tags: ["image", "hero"],
      variables: ["product", "style", "lighting"],
      version: 1,
      favorite: true,
      updatedAt: now,
      history: [],
    },
    {
      id: "cp_video_scene",
      title: "Video · Scene board",
      category: "video",
      body: "Outline a {{shots}}-shot scene board for {{narrative}} lasting {{duration}}s.",
      tags: ["video", "scene"],
      variables: ["shots", "narrative", "duration"],
      version: 1,
      favorite: false,
      updatedAt: now,
      history: [],
    },
    {
      id: "cp_avatar_talk",
      title: "Avatar · Presenter script",
      category: "avatar",
      body: "Script a presenter avatar for {{topic}} with tone {{tone}} and CTA {{cta}}.",
      tags: ["avatar", "presenter"],
      variables: ["topic", "tone", "cta"],
      version: 1,
      favorite: false,
      updatedAt: now,
      history: [],
    },
  ];
}

export function seedMedia(): MediaAsset[] {
  const now = new Date().toISOString();
  return [
    { id: "ma_hero", name: "Hero still v1", kind: "image", studioId: "image", tags: ["hero"], version: 1, status: "approved", updatedAt: now },
    { id: "ma_reel", name: "Reel cut 9:16", kind: "video", studioId: "reels", tags: ["reels"], version: 2, status: "draft", updatedAt: now },
    { id: "ma_vo", name: "VO English", kind: "audio", studioId: "voice", tags: ["voice"], version: 1, status: "approved", updatedAt: now },
    { id: "ma_brief", name: "Campaign brief", kind: "document", studioId: "creative", tags: ["brief"], version: 1, status: "draft", updatedAt: now },
    { id: "ma_tpl", name: "Ad template A", kind: "template", studioId: "templates", tags: ["ads"], version: 3, status: "approved", updatedAt: now },
    { id: "ma_logo", name: "Brand mark", kind: "brand", studioId: "brand", tags: ["logo"], version: 4, status: "approved", updatedAt: now },
    { id: "ma_font", name: "Display font", kind: "font", studioId: "brand", tags: ["type"], version: 1, status: "approved", updatedAt: now },
    { id: "ma_icon", name: "Icon set", kind: "icon", studioId: "assets", tags: ["ui"], version: 2, status: "approved", updatedAt: now },
    { id: "ma_anim", name: "Logo sting", kind: "animation", studioId: "video", tags: ["motion"], version: 1, status: "draft", updatedAt: now },
  ];
}

export function seedPipelines(): ProductionPipeline[] {
  const now = new Date().toISOString();
  return [
    {
      id: "pp_reel_01",
      title: "Launch reel · Q3",
      studioId: "reels",
      stage: "generation",
      agentChain: ["Hook Writer", "Reels Agent", "Brand Compliance"],
      promptId: "cp_reels_hook",
      mediaIds: ["ma_reel"],
      updatedAt: now,
    },
    {
      id: "pp_ads_01",
      title: "Paid pack · Offer",
      studioId: "ads",
      stage: "review",
      agentChain: ["Ads Agent", "Performance", "Compliance"],
      promptId: "cp_ad_variant",
      mediaIds: ["ma_tpl"],
      updatedAt: now,
    },
  ];
}

export function seedJobs(): AutomationJob[] {
  const now = new Date().toISOString();
  return [
    { id: "aj_batch_1", title: "Batch resize heroes", kind: "batch", status: "running", retries: 0, notify: true, pipelineId: "pp_reel_01", updatedAt: now },
    { id: "aj_queue_1", title: "Render queue · night", kind: "queue", status: "queued", retries: 0, notify: true, updatedAt: now },
    { id: "aj_sched_1", title: "Publish window · Fri 10:00", kind: "schedule", status: "queued", retries: 0, notify: true, scheduleAt: now, pipelineId: "pp_ads_01", updatedAt: now },
  ];
}

export function seedPromptCollections(): PromptCollection[] {
  const now = new Date().toISOString();
  return [
    {
      id: "pc_social",
      title: "Social shorts",
      category: "reels",
      promptIds: ["cp_reels_hook"],
      description: "Hooks and 9:16 openers",
      updatedAt: now,
    },
    {
      id: "pc_paid",
      title: "Paid media",
      category: "ads",
      promptIds: ["cp_ad_variant", "cp_brand_safe"],
      description: "Ads + brand-safe stills",
      updatedAt: now,
    },
    {
      id: "pc_voice",
      title: "Voice pack",
      category: "voice",
      promptIds: ["cp_voice_script"],
      description: "Narration and localization",
      updatedAt: now,
    },
  ];
}

export function seedProjects(): StudioProject[] {
  const now = new Date().toISOString();
  return [
    {
      id: "sp_launch_reel",
      title: "Launch reel · Q3",
      studioId: "reels",
      description: "Hero reel for product launch",
      favorite: true,
      pipelineIds: ["pp_reel_01"],
      mediaIds: ["ma_reel"],
      promptId: "cp_reels_hook",
      status: "active",
      updatedAt: now,
      createdAt: now,
    },
    {
      id: "sp_paid_pack",
      title: "Paid pack · Offer",
      studioId: "ads",
      description: "A/B creative pack",
      favorite: false,
      pipelineIds: ["pp_ads_01"],
      mediaIds: ["ma_tpl"],
      promptId: "cp_ad_variant",
      status: "active",
      updatedAt: now,
      createdAt: now,
    },
    {
      id: "sp_voice_demo",
      title: "Voice demo · EN",
      studioId: "voice",
      description: "Narration sample",
      favorite: true,
      pipelineIds: [],
      mediaIds: ["ma_vo"],
      promptId: "cp_voice_script",
      status: "draft",
      updatedAt: now,
      createdAt: now,
    },
  ];
}

export function seedGenerations(): GenerationRecord[] {
  const now = new Date().toISOString();
  return [
    {
      id: "gen_01",
      projectId: "sp_launch_reel",
      studioId: "reels",
      title: "Hook cut · v1",
      promptId: "cp_reels_hook",
      jobIds: [],
      mediaIds: ["ma_reel"],
      agents: ["Hook Writer", "Reels Agent"],
      status: "done",
      favorite: true,
      createdAt: now,
      updatedAt: now,
    },
    {
      id: "gen_02",
      projectId: "sp_paid_pack",
      studioId: "ads",
      title: "Variant pack · draft",
      promptId: "cp_ad_variant",
      jobIds: [],
      mediaIds: ["ma_tpl"],
      agents: ["Ads Agent"],
      status: "running",
      favorite: false,
      createdAt: now,
      updatedAt: now,
    },
  ];
}
