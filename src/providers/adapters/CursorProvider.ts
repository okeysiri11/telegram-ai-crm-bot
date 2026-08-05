import { BaseProvider } from "../BaseProvider.js";
import type { ProviderExecuteRequest } from "../types.js";

export interface CursorFileWrite {
  readonly path: string;
  readonly content: string;
}

export interface CursorWorkspaceState {
  workspace: string;
  open: boolean;
  files: Map<string, string>;
  tasks: Array<Record<string, unknown>>;
  commits: string[];
  lastCommand?: string;
}

/**
 * Cursor Provider — mock IDE API that is fully functional in-process.
 * No real Cursor binary required; tracks workspace/files/commands/commits.
 */
export class CursorProvider extends BaseProvider {
  private readonly state: CursorWorkspaceState = {
    workspace: "",
    open: false,
    files: new Map(),
    tasks: [],
    commits: [],
  };

  constructor() {
    super({
      id: "provider.cursor",
      name: "Cursor Provider",
      kind: "ide-ai",
      baseUrl: "mock://cursor",
      models: ["cursor-composer", "cursor-fast"],
      capabilities: [
        { id: "code.complete", description: "Code completion" },
        { id: "code.edit", description: "Inline edits" },
        { id: "chat", description: "Agent chat" },
        { id: "workspace", description: "Workspace operations" },
        { id: "build", description: "Run builds" },
        { id: "test", description: "Run tests" },
      ],
    });
  }

  async createTask(input: {
    id: string;
    title: string;
    description: string;
    kind?: string;
  }): Promise<Record<string, unknown>> {
    const task = {
      id: input.id,
      title: input.title,
      description: input.description,
      kind: input.kind ?? "code",
      createdAt: new Date().toISOString(),
      status: "open",
    };
    this.state.tasks.push(task);
    return { ...task, provider: this.id };
  }

  async openWorkspace(path: string): Promise<Record<string, unknown>> {
    this.state.workspace = path;
    this.state.open = true;
    return {
      ok: true,
      workspace: path,
      open: true,
      provider: this.id,
    };
  }

  async writeFiles(
    files: readonly CursorFileWrite[],
  ): Promise<Record<string, unknown>> {
    const filesWritten: string[] = [];
    for (const f of files) {
      this.state.files.set(f.path, f.content);
      filesWritten.push(f.path);
    }
    return {
      ok: true,
      filesWritten,
      count: filesWritten.length,
      provider: this.id,
    };
  }

  async applyPatch(patch: string): Promise<Record<string, unknown>> {
    const addMatch = patch.match(/\*\*\* Add File: (.+)/);
    if (addMatch?.[1] && !this.state.files.has(addMatch[1].trim())) {
      this.state.files.set(addMatch[1].trim(), patch);
    }
    return {
      ok: true,
      applied: true,
      bytes: patch.length,
      provider: this.id,
    };
  }

  async runBuild(): Promise<Record<string, unknown>> {
    return {
      ok: true,
      command: "npm run build",
      exitCode: 0,
      durationMs: 12,
      provider: this.id,
    };
  }

  async runTests(): Promise<Record<string, unknown>> {
    return {
      ok: true,
      command: "npm test",
      exitCode: 0,
      passed: true,
      durationMs: 18,
      provider: this.id,
    };
  }

  async runCommand(cmd: string): Promise<Record<string, unknown>> {
    this.state.lastCommand = cmd;
    return {
      ok: true,
      command: cmd,
      stdout: `[cursor] executed: ${cmd}`,
      exitCode: 0,
      provider: this.id,
    };
  }

  async commit(message: string): Promise<Record<string, unknown>> {
    const sha = `c${Date.now().toString(36)}`;
    this.state.commits.push(`${sha} ${message}`);
    return {
      ok: true,
      sha,
      message,
      files: [...this.state.files.keys()],
      provider: this.id,
    };
  }

  getWorkspaceSnapshot(): Record<string, unknown> {
    return {
      workspace: this.state.workspace,
      open: this.state.open,
      files: Object.fromEntries(this.state.files.entries()),
      tasks: [...this.state.tasks],
      commits: [...this.state.commits],
      lastCommand: this.state.lastCommand ?? null,
    };
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      model: "cursor-composer",
      mock: true,
      capability: request.capability,
      text: `[Cursor] Handled ${request.capability}`,
      workspace: this.state.workspace || null,
      filesTracked: this.state.files.size,
      input: request.input,
    };
  }
}
