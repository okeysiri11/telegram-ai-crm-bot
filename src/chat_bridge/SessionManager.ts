import type { ChatTask, ProjectContext } from "./types.js";

export interface SessionSnapshot {
  readonly id: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly conversation: Array<{ role: "user" | "assistant" | "system"; content: string; at: string }>;
  readonly generatedFiles: readonly string[];
  readonly affectedModules: readonly string[];
  readonly previousPrompts: readonly string[];
  readonly architectureDecisions: readonly string[];
  readonly projectContext: ProjectContext;
  readonly taskIds: readonly string[];
}

/**
 * Session memory across ChatGPT ↔ ADOS ↔ Cursor exchanges.
 */
export class SessionManager {
  private readonly sessions = new Map<string, SessionState>();
  private activeId: string;

  constructor() {
    this.activeId = this.createSession().id;
  }

  get activeSessionId(): string {
    return this.activeId;
  }

  createSession(projectContext?: Partial<ProjectContext>): SessionSnapshot {
    const id = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    const now = new Date().toISOString();
    const state: SessionState = {
      id,
      createdAt: now,
      updatedAt: now,
      conversation: [],
      generatedFiles: [],
      affectedModules: [],
      previousPrompts: [],
      architectureDecisions: [],
      taskIds: [],
      projectContext: {
        project: projectContext?.project ?? "ADOS Enterprise OS",
        repository: projectContext?.repository ?? "TelegramBotCourse",
        sprint: projectContext?.sprint ?? "ADOS OS 4.0",
        affectedModules: [...(projectContext?.affectedModules ?? [])],
        relatedFiles: [...(projectContext?.relatedFiles ?? [])],
        dependencies: [...(projectContext?.dependencies ?? [])],
      },
    };
    this.sessions.set(id, state);
    this.activeId = id;
    return this.snapshot(state);
  }

  get(id?: string): SessionSnapshot {
    const state = this.sessions.get(id ?? this.activeId);
    if (!state) throw new Error(`Session not found: ${id ?? this.activeId}`);
    return this.snapshot(state);
  }

  appendUser(prompt: string, sessionId?: string): void {
    const s = this.require(sessionId);
    s.conversation.push({
      role: "user",
      content: prompt,
      at: new Date().toISOString(),
    });
    s.previousPrompts.push(prompt);
    s.updatedAt = new Date().toISOString();
  }

  appendAssistant(content: string, sessionId?: string): void {
    const s = this.require(sessionId);
    s.conversation.push({
      role: "assistant",
      content,
      at: new Date().toISOString(),
    });
    s.updatedAt = new Date().toISOString();
  }

  recordTask(task: ChatTask, sessionId?: string): void {
    const s = this.require(sessionId);
    s.taskIds.push(task.id);
    for (const m of task.context.affectedModules) {
      if (!s.affectedModules.includes(m)) s.affectedModules.push(m);
    }
    for (const f of task.generatedFiles) {
      if (!s.generatedFiles.includes(f)) s.generatedFiles.push(f);
    }
    if (task.kind === "architecture" && task.result) {
      s.architectureDecisions.push(
        typeof task.result === "string"
          ? task.result
          : JSON.stringify(task.result).slice(0, 500),
      );
    }
    s.updatedAt = new Date().toISOString();
  }

  addGeneratedFiles(files: readonly string[], sessionId?: string): void {
    const s = this.require(sessionId);
    for (const f of files) {
      if (!s.generatedFiles.includes(f)) s.generatedFiles.push(f);
    }
    s.updatedAt = new Date().toISOString();
  }

  private require(sessionId?: string): SessionState {
    const id = sessionId ?? this.activeId;
    const s = this.sessions.get(id);
    if (!s) throw new Error(`Session not found: ${id}`);
    return s;
  }

  private snapshot(s: SessionState): SessionSnapshot {
    return {
      id: s.id,
      createdAt: s.createdAt,
      updatedAt: s.updatedAt,
      conversation: [...s.conversation],
      generatedFiles: [...s.generatedFiles],
      affectedModules: [...s.affectedModules],
      previousPrompts: [...s.previousPrompts],
      architectureDecisions: [...s.architectureDecisions],
      projectContext: {
        ...s.projectContext,
        affectedModules: [...s.projectContext.affectedModules],
        relatedFiles: [...s.projectContext.relatedFiles],
        dependencies: [...s.projectContext.dependencies],
      },
      taskIds: [...s.taskIds],
    };
  }
}

interface SessionState {
  id: string;
  createdAt: string;
  updatedAt: string;
  conversation: Array<{ role: "user" | "assistant" | "system"; content: string; at: string }>;
  generatedFiles: string[];
  affectedModules: string[];
  previousPrompts: string[];
  architectureDecisions: string[];
  taskIds: string[];
  projectContext: ProjectContext;
}

export function createSessionManager(): SessionManager {
  return new SessionManager();
}
