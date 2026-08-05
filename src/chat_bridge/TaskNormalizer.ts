import type { ParsedPrompt } from "./types.js";
import type {
  ChatAttachment,
  ChatTask,
  ProjectContext,
} from "./types.js";

export interface NormalizeInput {
  readonly prompt: string;
  readonly parsed: ParsedPrompt;
  readonly attachments?: readonly ChatAttachment[];
  readonly provider?: string;
  readonly projectContext?: Partial<ProjectContext>;
  readonly sessionId?: string;
}

const DEFAULT_CONTEXT: ProjectContext = {
  project: "ADOS Enterprise OS",
  repository: "TelegramBotCourse",
  sprint: "ADOS OS 4.0",
  affectedModules: ["src/chat_bridge", "src/orchestrator", "src/providers"],
  relatedFiles: [],
  dependencies: ["@ados/orchestrator", "@ados/providers", "@ados/kernel"],
};

/**
 * Builds a full ChatTask with automatic enterprise project context.
 */
export class TaskNormalizer {
  private seq = 0;

  normalize(input: NormalizeInput): ChatTask {
    this.seq += 1;
    const id = `chat_${Date.now().toString(36)}_${this.seq}`;
    const now = new Date().toISOString();
    const ctx: ProjectContext = {
      project: input.projectContext?.project ?? DEFAULT_CONTEXT.project,
      repository: input.projectContext?.repository ?? DEFAULT_CONTEXT.repository,
      sprint: input.projectContext?.sprint ?? DEFAULT_CONTEXT.sprint,
      affectedModules: unique([
        ...DEFAULT_CONTEXT.affectedModules,
        ...(input.projectContext?.affectedModules ?? []),
        ...input.parsed.modules,
      ]),
      relatedFiles: unique([
        ...(input.projectContext?.relatedFiles ?? []),
        ...input.parsed.files,
      ]),
      dependencies: unique([
        ...DEFAULT_CONTEXT.dependencies,
        ...(input.projectContext?.dependencies ?? []),
      ]),
    };

    return {
      id,
      title: input.parsed.title,
      description: input.parsed.description,
      kind: input.parsed.kind,
      context: ctx,
      priority: input.parsed.priority,
      attachments: input.attachments ?? [],
      files: input.parsed.files,
      provider: input.provider ?? "provider.cursor",
      preferredAgent: input.parsed.preferredAgent,
      status: "Queued",
      createdAt: now,
      updatedAt: now,
      rawPrompt: input.prompt,
      retries: 0,
      generatedFiles: [],
    };
  }
}

function unique(items: readonly string[]): string[] {
  return [...new Set(items.filter(Boolean))];
}

export function createTaskNormalizer(): TaskNormalizer {
  return new TaskNormalizer();
}
