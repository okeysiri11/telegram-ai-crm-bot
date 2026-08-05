/**
 * Sprint 32.0 — Content types mapped onto existing Production studios.
 * Publish targets (stories/posts) reuse social studios — no new engines.
 */

import type { ProductionStudioId } from "./productionCatalog";

export type ContentTypeId =
  | "text"
  | "images"
  | "video"
  | "reels"
  | "stories"
  | "posts"
  | "ads"
  | "presentations"
  | "landing_pages"
  | "email_campaigns"
  | "pdf";

export type ContentTypeDef = {
  id: ContentTypeId;
  label: string;
  labelRu: string;
  studioId: ProductionStudioId;
  /** Primary provider category hint for ProductionProviderStrip */
  providerHint: "ai" | "image" | "video" | "audio";
};

export const CONTENT_TYPES: ContentTypeDef[] = [
  { id: "text", label: "Text", labelRu: "Текст", studioId: "prompt", providerHint: "ai" },
  { id: "images", label: "Images", labelRu: "Изображения", studioId: "image", providerHint: "image" },
  { id: "video", label: "Video", labelRu: "Видео", studioId: "video", providerHint: "video" },
  { id: "reels", label: "Reels", labelRu: "Reels", studioId: "reels", providerHint: "video" },
  { id: "stories", label: "Stories", labelRu: "Stories", studioId: "instagram", providerHint: "image" },
  { id: "posts", label: "Posts", labelRu: "Посты", studioId: "creative", providerHint: "ai" },
  { id: "ads", label: "Ads", labelRu: "Реклама", studioId: "ads", providerHint: "ai" },
  { id: "presentations", label: "Presentations", labelRu: "Презентации", studioId: "presentation", providerHint: "ai" },
  { id: "landing_pages", label: "Landing Pages", labelRu: "Лендинги", studioId: "creative", providerHint: "ai" },
  { id: "email_campaigns", label: "Email Campaigns", labelRu: "Email", studioId: "creative", providerHint: "ai" },
  { id: "pdf", label: "PDF", labelRu: "PDF", studioId: "templates", providerHint: "ai" },
];

export function contentTypeById(id: ContentTypeId): ContentTypeDef | undefined {
  return CONTENT_TYPES.find((c) => c.id === id);
}

/** Production Home navigation — maps to ProductionView / studio routes. */
export const PRODUCTION_HOME_NAV = [
  { id: "home", label: "Production Home", labelRu: "Главная", view: "home" as const },
  { id: "projects", label: "Projects", labelRu: "Проекты", view: "projects" as const },
  { id: "tasks", label: "Tasks", labelRu: "Задачи", view: "runtime" as const },
  { id: "assets", label: "Assets", labelRu: "Ассеты", view: "assets" as const },
  { id: "templates", label: "Templates", labelRu: "Шаблоны", view: "templates" as const },
  { id: "media", label: "Media Library", labelRu: "Медиатека", view: "media" as const },
  { id: "brand", label: "Brand Library", labelRu: "Бренд", view: "brand" as const },
  { id: "prompts", label: "Prompt Library", labelRu: "Промпты", view: "prompts" as const },
  { id: "ai_queue", label: "AI Queue", labelRu: "AI-очередь", view: "queue" as const },
  { id: "render_queue", label: "Render Queue", labelRu: "Рендер", view: "queue" as const, queue: "render" as const },
  { id: "history", label: "Generation History", labelRu: "История", view: "history" as const },
  { id: "pipeline", label: "Workflow Builder", labelRu: "Конвейер", view: "pipeline" as const },
] as const;
