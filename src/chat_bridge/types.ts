/**
 * ChatGPT Bridge types — ChatGPT → ADOS → Cursor middleware.
 */

export type ChatTaskKind =
  | "architecture"
  | "code"
  | "refactor"
  | "bugfix"
  | "documentation"
  | "research"
  | "testing"
  | "deployment";

export type ChatTaskStatus =
  | "Queued"
  | "Running"
  | "Waiting"
  | "Review"
  | "Done"
  | "Failed"
  | "Cancelled"
  | "PartialSuccess";

export type ChatPriority = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export interface ProjectContext {
  readonly project: string;
  readonly repository: string;
  readonly sprint: string;
  readonly affectedModules: readonly string[];
  readonly relatedFiles: readonly string[];
  readonly dependencies: readonly string[];
}

export interface ChatAttachment {
  readonly name: string;
  readonly mimeType?: string;
  readonly content?: string;
  readonly url?: string;
}

export interface ChatTask {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly kind: ChatTaskKind;
  readonly context: ProjectContext;
  readonly priority: ChatPriority;
  readonly attachments: readonly ChatAttachment[];
  readonly files: readonly string[];
  readonly provider: string;
  readonly preferredAgent: string;
  status: ChatTaskStatus;
  readonly createdAt: string;
  updatedAt: string;
  readonly rawPrompt: string;
  result?: unknown;
  error?: string;
  durationMs?: number;
  retries: number;
  generatedFiles: string[];
  collaborationWorkflowId?: string;
}

export interface PromptHistoryEntry {
  readonly id: string;
  readonly at: string;
  readonly prompt: string;
  readonly provider: string;
  readonly result?: unknown;
  readonly durationMs?: number;
  readonly status: ChatTaskStatus | "received" | "parsed";
  readonly taskId?: string;
  readonly agentId?: string;
}

export interface ParsedPrompt {
  readonly kind: ChatTaskKind;
  readonly title: string;
  readonly description: string;
  readonly priority: ChatPriority;
  readonly preferredAgent: string;
  readonly files: readonly string[];
  readonly modules: readonly string[];
  readonly confidence: number;
}

export type ChatBridgeEventType =
  | "chat.received"
  | "task.created"
  | "task.started"
  | "task.completed"
  | "provider.started"
  | "provider.finished"
  | "review.started"
  | "review.completed";
