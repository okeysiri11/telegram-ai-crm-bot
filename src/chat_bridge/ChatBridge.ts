import type { AiOrchestrator } from "@ados/orchestrator";
import type { ProviderGateway } from "@ados/providers";
import { CommandQueue, createCommandQueue } from "./CommandQueue.js";
import { PromptHistory } from "./PromptHistory.js";
import { PromptParser, createPromptParser } from "./PromptParser.js";
import { SessionManager, createSessionManager } from "./SessionManager.js";
import { TaskNormalizer, createTaskNormalizer } from "./TaskNormalizer.js";
import { createVoiceReadyContracts } from "./voice/VoiceContracts.js";
import type {
  ChatAttachment,
  ChatBridgeEventType,
  ChatTask,
  ProjectContext,
} from "./types.js";

export type ChatBridgeListener = (event: {
  type: ChatBridgeEventType;
  payload: unknown;
}) => void;

export interface ChatBridgeOptions {
  readonly orchestrator: AiOrchestrator;
  readonly gateway: ProviderGateway;
  readonly maxRetries?: number;
}

/**
 * ChatGPT → ADOS → Cursor middleware.
 * Ingests prompts, normalizes tasks, routes via Orchestrator, executes via Cursor Provider.
 */
export class ChatBridge {
  readonly parser: PromptParser;
  readonly normalizer: TaskNormalizer;
  readonly history: PromptHistory;
  readonly sessions: SessionManager;
  readonly queue: CommandQueue;
  readonly voice = createVoiceReadyContracts();

  private readonly orchestrator: AiOrchestrator;
  private readonly gateway: ProviderGateway;
  private readonly maxRetries: number;
  private readonly listeners = new Set<ChatBridgeListener>();
  private processing = false;

  constructor(options: ChatBridgeOptions) {
    this.orchestrator = options.orchestrator;
    this.gateway = options.gateway;
    this.maxRetries = options.maxRetries ?? 2;
    this.parser = createPromptParser();
    this.normalizer = createTaskNormalizer();
    this.history = new PromptHistory();
    this.sessions = createSessionManager();
    this.queue = createCommandQueue();
  }

  on(listener: ChatBridgeListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Receive ChatGPT text, create a queued ChatTask (does not auto-run).
   */
  ingest(input: {
    prompt: string;
    attachments?: readonly ChatAttachment[];
    provider?: string;
    projectContext?: Partial<ProjectContext>;
    sessionId?: string;
    autoRun?: boolean;
  }): ChatTask {
    const prompt = input.prompt.trim();
    this.emit("chat.received", { prompt, at: new Date().toISOString() });
    this.history.push({
      prompt,
      provider: input.provider ?? "chatgpt",
      status: "received",
    });

    this.sessions.appendUser(prompt, input.sessionId);
    const parsed = this.parser.parse(prompt);
    const task = this.normalizer.normalize({
      prompt,
      parsed,
      ...(input.attachments !== undefined ? { attachments: input.attachments } : {}),
      provider: input.provider ?? "provider.cursor",
      ...(input.projectContext !== undefined
        ? { projectContext: input.projectContext }
        : { projectContext: this.sessions.get(input.sessionId).projectContext }),
      ...(input.sessionId !== undefined ? { sessionId: input.sessionId } : {}),
    });

    this.queue.enqueue(task);
    this.sessions.recordTask(task, input.sessionId);
    this.history.push({
      prompt,
      provider: task.provider,
      status: "parsed",
      taskId: task.id,
      agentId: task.preferredAgent,
    });
    this.emit("task.created", task);

    if (input.autoRun !== false) {
      void this.run(task.id).catch(() => undefined);
    }
    return task;
  }

  /** Alias used by API POST /chat/task */
  createTask(input: {
    prompt: string;
    attachments?: readonly ChatAttachment[];
    provider?: string;
    projectContext?: Partial<ProjectContext>;
    sessionId?: string;
    autoRun?: boolean;
  }): ChatTask {
    return this.ingest({ ...input, autoRun: input.autoRun ?? false });
  }

  /** Execute a queued task end-to-end. */
  async run(taskId?: string): Promise<ChatTask> {
    const task =
      (taskId ? this.queue.get(taskId) : this.queue.nextQueued()) ??
      undefined;
    if (!task) throw new Error("No queued chat task to run");

    this.queue.setStatus(task.id, "Running");
    this.emit("task.started", task);
    const started = Date.now();

    try {
      // 1) Cursor provider workspace + files
      this.emit("provider.started", {
        providerId: task.provider,
        taskId: task.id,
      });
      const cursor = await this.executeCursor(task);
      this.emit("provider.finished", {
        providerId: task.provider,
        taskId: task.id,
        result: cursor,
      });

      // 2) Orchestrator agent work
      const agentResult = await this.orchestrator.runAgent(task.preferredAgent, {
        type: task.kind,
        task: task.title,
        payload: {
          description: task.description,
          context: task.context,
          cursor,
          files: task.files,
        },
        provider: "cursor",
      });

      // 3) Review stage
      this.queue.setStatus(task.id, "Review");
      this.emit("review.started", { taskId: task.id });
      const review = await this.orchestrator.runAgent("agent.reviewer", {
        type: "review.code",
        task: `Review ${task.title}`,
        payload: {
          taskId: task.id,
          title: task.title,
          kind: task.kind,
          agentOk: agentResult.ok,
          filesWritten: cursor.filesWritten,
        },
      });
      this.emit("review.completed", { taskId: task.id, review: summarizeAgentResult(review) });

      // 4) Optional QA for code/bugfix/testing
      let qa: unknown = null;
      if (
        task.kind === "code" ||
        task.kind === "bugfix" ||
        task.kind === "testing" ||
        task.kind === "refactor"
      ) {
        qa = await this.orchestrator.runAgent("agent.qa", {
          type: "qa.test",
          task: `QA ${task.title}`,
          payload: {
            taskId: task.id,
            title: task.title,
            kind: task.kind,
            agentOk: agentResult.ok,
          },
        });
      }

      const generatedFiles = Array.isArray(cursor.filesWritten)
        ? (cursor.filesWritten as string[])
        : [];
      task.generatedFiles = generatedFiles;
      this.sessions.addGeneratedFiles(generatedFiles);
      this.sessions.appendAssistant(
        `Completed ${task.title} via ${task.preferredAgent}`,
      );

      const durationMs = Date.now() - started;
      const ok = agentResult.ok && review.ok;
      const status = ok
        ? "Done"
        : agentResult.ok || review.ok
          ? "PartialSuccess"
          : "Failed";

      const updated = this.queue.update(task.id, {
        status,
        durationMs,
        result: toJsonSafe({
          agent: summarizeAgentResult(agentResult),
          review: summarizeAgentResult(review),
          qa: qa ? summarizeAgentResult(qa as { ok: boolean; agentId?: string; error?: string; durationMs?: number; output?: unknown }) : null,
          cursor: {
            filesWritten: generatedFiles,
            build: cursor.build,
            tests: cursor.tests,
            commit: cursor.commit,
            cmd: cursor.cmd,
          },
          generatedFiles,
        }),
        ...(ok ? {} : { error: agentResult.error ?? review.error ?? "Failed" }),
      });

      this.history.push({
        prompt: task.rawPrompt,
        provider: task.provider,
        status: updated.status,
        taskId: task.id,
        agentId: task.preferredAgent,
        durationMs,
        result: updated.result,
      });
      this.emit("task.completed", updated);
      return updated;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (task.retries < this.maxRetries) {
        task.retries += 1;
        this.queue.setStatus(task.id, "Queued");
        this.queue.update(task.id, { error: message });
        return this.run(task.id);
      }
      const failed = this.queue.update(task.id, {
        status: "Failed",
        error: message,
        durationMs: Date.now() - started,
      });
      this.history.push({
        prompt: task.rawPrompt,
        provider: task.provider,
        status: "Failed",
        taskId: task.id,
        durationMs: failed.durationMs ?? Date.now() - started,
        result: { error: message },
      });
      this.emit("task.completed", failed);
      return failed;
    }
  }

  /** Process queue head if idle. */
  async processQueue(): Promise<ChatTask | null> {
    if (this.processing) return null;
    const next = this.queue.nextQueued();
    if (!next) return null;
    this.processing = true;
    try {
      return await this.run(next.id);
    } finally {
      this.processing = false;
    }
  }

  async cancel(taskId: string): Promise<ChatTask> {
    return this.queue.setStatus(taskId, "Cancelled");
  }

  async rollback(taskId: string): Promise<ChatTask> {
    const task = this.queue.get(taskId);
    if (!task) throw new Error(`Task not found: ${taskId}`);
    // Functional rollback: clear generated files from session tracking, requeue
    task.generatedFiles = [];
    task.result = { rolledBack: true, previous: task.result };
    delete task.error;
    task.retries = 0;
    return this.queue.update(taskId, { status: "Queued" });
  }

  status() {
    const q = this.queue.snapshot();
    const session = this.sessions.get();
    const current = q.tasks.find((t) => t.status === "Running") ?? q.tasks[0];
    return {
      id: "ados.chat_bridge",
      name: "ChatGPT Bridge",
      health: "OK" as const,
      voiceReady: this.voice.supported && this.voice.implemented,
      queue: {
        total: q.total,
        queued: q.queued,
        running: q.running,
        done: q.done,
        failed: q.failed,
      },
      currentPrompt: current?.rawPrompt ?? null,
      currentTask: current ?? null,
      currentProvider: current?.provider ?? "provider.cursor",
      currentAgent: current?.preferredAgent ?? null,
      generatedFiles: session.generatedFiles,
      sessionId: session.id,
    };
  }

  private async executeCursor(task: ChatTask): Promise<Record<string, unknown>> {
    // Ensure cursor connected
    const provider = this.gateway.selectProvider({
      preferredId: task.provider,
      preferredAlias: "cursor",
      capability: "code.edit",
    });
    if (!provider.snapshot().connected) {
      await provider.connect();
    }

    // Prefer Cursor IDE API when available (CursorProvider extended)
    const cursorApi = provider as unknown as {
      createTask?: (input: unknown) => Promise<unknown>;
      openWorkspace?: (path: string) => Promise<unknown>;
      writeFiles?: (files: Array<{ path: string; content: string }>) => Promise<unknown>;
      applyPatch?: (patch: string) => Promise<unknown>;
      runBuild?: () => Promise<unknown>;
      runTests?: () => Promise<unknown>;
      runCommand?: (cmd: string) => Promise<unknown>;
      commit?: (message: string) => Promise<unknown>;
    };

    const workspace =
      (await cursorApi.openWorkspace?.("/Users/macbook/Desktop/TelegramBotCourse")) ??
      { workspace: "TelegramBotCourse", mock: true };

    const cursorTask =
      (await cursorApi.createTask?.({
        id: task.id,
        title: task.title,
        description: task.description,
        kind: task.kind,
      })) ?? { id: task.id, created: true };

    const filePath =
      task.files[0] ??
      `generated/chat/${task.id.replace(/[^a-z0-9_]/gi, "_")}.md`;
    const content = [
      `# ${task.title}`,
      "",
      `Kind: ${task.kind}`,
      `Agent: ${task.preferredAgent}`,
      `Sprint: ${task.context.sprint}`,
      "",
      task.description,
      "",
      "## Project Context",
      `- Project: ${task.context.project}`,
      `- Repository: ${task.context.repository}`,
      `- Modules: ${task.context.affectedModules.join(", ")}`,
      `- Related: ${task.context.relatedFiles.join(", ") || "n/a"}`,
      `- Dependencies: ${task.context.dependencies.join(", ")}`,
    ].join("\n");

    const written =
      (await cursorApi.writeFiles?.([{ path: filePath, content }])) ??
      ({ filesWritten: [filePath], mock: true } as Record<string, unknown>);

    await cursorApi.applyPatch?.(
      `*** Begin Patch\n*** Add File: ${filePath}\n+${content.split("\n").join("\n+")}\n*** End Patch`,
    );

    const build = (await cursorApi.runBuild?.()) ?? { ok: true, mock: true };
    const tests = (await cursorApi.runTests?.()) ?? { ok: true, mock: true };
    const cmd =
      (await cursorApi.runCommand?.("echo ados-chat-bridge")) ??
      { ok: true, stdout: "ados-chat-bridge" };
    const commit =
      (await cursorApi.commit?.(`ADOS chat: ${task.title}`)) ??
      { ok: true, sha: `mock_${task.id}` };

    // Also go through gateway.execute for metrics/events
    const gwResult = await this.gateway.execute({
      preferredAlias: "cursor",
      capability: "code.edit",
      payload: {
        taskId: task.id,
        title: task.title,
        filePath,
      },
    });

    const filesWritten = Array.isArray(
      (written as { filesWritten?: string[] }).filesWritten,
    )
      ? (written as { filesWritten: string[] }).filesWritten
      : [filePath];

    return {
      workspace,
      cursorTask,
      filesWritten,
      build,
      tests,
      cmd,
      commit,
      gateway: gwResult,
    };
  }

  private emit(type: ChatBridgeEventType, payload: unknown): void {
    for (const listener of this.listeners) {
      try {
        listener({ type, payload });
      } catch {
        /* ignore */
      }
    }
  }
}

export function createChatBridge(options: ChatBridgeOptions): ChatBridge {
  return new ChatBridge(options);
}

function summarizeAgentResult(result: {
  ok: boolean;
  agentId?: string;
  error?: string;
  durationMs?: number;
  output?: unknown;
}): Record<string, unknown> {
  return {
    ok: result.ok,
    ...(result.agentId !== undefined ? { agentId: result.agentId } : {}),
    ...(result.error !== undefined ? { error: result.error } : {}),
    ...(result.durationMs !== undefined ? { durationMs: result.durationMs } : {}),
    output: toJsonSafe(result.output ?? null),
  };
}

/** Strip circular refs so REST/WS can serialize task results. */
function toJsonSafe(value: unknown): unknown {
  const seen = new WeakSet<object>();
  try {
    return JSON.parse(
      JSON.stringify(value, (_key, current) => {
        if (typeof current === "object" && current !== null) {
          if (seen.has(current)) return "[Circular]";
          seen.add(current);
        }
        return current;
      }),
    );
  } catch {
    return { note: "unserializable" };
  }
}
