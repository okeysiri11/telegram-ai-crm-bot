/**
 * Universal Production Pipelines — Sprint 28.2.
 * Templates only; execution goes through Job Manager + Production Runtime.
 */

import type { UniversalPipelineId, ProductionQueueKind } from "./types";

export type UniversalPipelineDef = {
  id: UniversalPipelineId;
  label: string;
  studioId: string;
  description: string;
  /** Default queue lane for generation work. */
  primaryQueue: ProductionQueueKind;
  /** Agent names (resolved against aiAgentRuntime / studio catalog). */
  defaultAgents: string[];
  stages: Array<"draft" | "review" | "approval" | "generation" | "render" | "publish" | "archive">;
  collaboration: "single" | "chain" | "multi";
};

export const UNIVERSAL_PIPELINES: UniversalPipelineDef[] = [
  {
    id: "image_generation",
    label: "Image Generation",
    studioId: "image",
    description: "Still images · variants · brand-safe crops",
    primaryQueue: "generation",
    defaultAgents: ["Creative Director", "Brand Compliance"],
    stages: ["draft", "review", "approval", "generation", "render", "publish", "archive"],
    collaboration: "chain",
  },
  {
    id: "video_generation",
    label: "Video Generation",
    studioId: "video",
    description: "Clips · timelines · scene boards",
    primaryQueue: "generation",
    defaultAgents: ["Video Director", "Editor Agent"],
    stages: ["draft", "review", "approval", "generation", "render", "publish", "archive"],
    collaboration: "multi",
  },
  {
    id: "audio_generation",
    label: "Audio Generation",
    studioId: "audio",
    description: "Beds · SFX · mix stems",
    primaryQueue: "generation",
    defaultAgents: ["Audio Agent"],
    stages: ["draft", "review", "generation", "render", "publish", "archive"],
    collaboration: "single",
  },
  {
    id: "voice_generation",
    label: "Voice Generation",
    studioId: "voice",
    description: "TTS · clone · localization",
    primaryQueue: "generation",
    defaultAgents: ["Voice Agent", "Localization"],
    stages: ["draft", "review", "approval", "generation", "publish", "archive"],
    collaboration: "chain",
  },
  {
    id: "avatar_generation",
    label: "Avatar Generation",
    studioId: "avatar",
    description: "Presenters · lip-sync · consent metadata",
    primaryQueue: "render",
    defaultAgents: ["Avatar Agent", "Compliance"],
    stages: ["draft", "review", "approval", "generation", "render", "publish", "archive"],
    collaboration: "multi",
  },
  {
    id: "reels_generation",
    label: "Reels Generation",
    studioId: "reels",
    description: "9:16 social shorts pipeline",
    primaryQueue: "generation",
    defaultAgents: ["Reels Agent", "Hook Writer", "Brand Compliance"],
    stages: ["draft", "review", "approval", "generation", "render", "publish", "archive"],
    collaboration: "multi",
  },
  {
    id: "campaign_generation",
    label: "Campaign Generation",
    studioId: "ads",
    description: "Paid creative packs · A/B variants",
    primaryQueue: "production",
    defaultAgents: ["Ads Agent", "Performance", "Compliance"],
    stages: ["draft", "review", "approval", "generation", "render", "publish", "archive"],
    collaboration: "multi",
  },
  {
    id: "publishing",
    label: "Publishing",
    studioId: "publishing",
    description: "Channels · approval gate · schedule",
    primaryQueue: "publishing",
    defaultAgents: ["Publisher", "Compliance"],
    stages: ["draft", "review", "approval", "publish", "archive"],
    collaboration: "chain",
  },
];

export function universalPipelineById(id: UniversalPipelineId): UniversalPipelineDef | undefined {
  return UNIVERSAL_PIPELINES.find((p) => p.id === id);
}

export function universalPipelineForStudio(studioId: string): UniversalPipelineDef | undefined {
  const direct = UNIVERSAL_PIPELINES.find((p) => p.studioId === studioId);
  if (direct) return direct;
  if (studioId === "presentation") return universalPipelineById("campaign_generation");
  if (studioId === "tiktok" || studioId === "instagram") return universalPipelineById("reels_generation");
  if (studioId === "youtube") return universalPipelineById("video_generation");
  if (studioId === "prompt" || studioId === "brand" || studioId === "assets") {
    return universalPipelineById("image_generation");
  }
  return undefined;
}
