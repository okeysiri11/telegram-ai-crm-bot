import { BaseProvider } from "../BaseProvider.js";
import type { ProviderExecuteRequest } from "../types.js";
import { CursorProvider } from "./CursorProvider.js";

export { CursorProvider } from "./CursorProvider.js";

export class OpenAIProvider extends BaseProvider {
  constructor() {
    super({
      id: "provider.openai",
      name: "OpenAI Provider",
      kind: "llm",
      baseUrl: "mock://openai",
      models: ["gpt-4.1-mini", "gpt-4.1"],
      capabilities: [
        { id: "chat", description: "Chat completions" },
        { id: "completion", description: "Text completion" },
        { id: "embeddings", description: "Embeddings" },
      ],
    });
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      model: "gpt-4.1-mini",
      mock: true,
      capability: request.capability,
      choices: [
        {
          message: {
            role: "assistant",
            content: `[OpenAI mock] ${request.capability}`,
          },
        },
      ],
      input: request.input,
    };
  }
}

export class ClaudeProvider extends BaseProvider {
  constructor() {
    super({
      id: "provider.claude",
      name: "Claude Provider",
      kind: "llm",
      baseUrl: "mock://anthropic",
      models: ["claude-sonnet", "claude-haiku"],
      capabilities: [
        { id: "chat", description: "Messages API" },
        { id: "completion", description: "Long-context completion" },
        { id: "analysis", description: "Document analysis" },
      ],
    });
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      model: "claude-sonnet",
      mock: true,
      capability: request.capability,
      content: [{ type: "text", text: `[Claude mock] ${request.capability}` }],
      input: request.input,
    };
  }
}

export class GitHubProvider extends BaseProvider {
  constructor() {
    super({
      id: "provider.github",
      name: "GitHub Copilot Provider",
      kind: "vcs-ai",
      baseUrl: "mock://github-copilot",
      capabilities: [
        { id: "repo.read", description: "Read repositories" },
        { id: "pr.create", description: "Create pull requests" },
        { id: "code.complete", description: "Copilot completions" },
        { id: "search", description: "Code search" },
      ],
    });
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      mock: true,
      capability: request.capability,
      result: `[GitHub mock] ${request.capability}`,
      input: request.input,
    };
  }
}

export class LocalLlmProvider extends BaseProvider {
  constructor() {
    super({
      id: "provider.local",
      name: "Local LLM Provider",
      kind: "llm-local",
      baseUrl: "mock://localhost:11434",
      models: ["local-small", "local-instruct"],
      capabilities: [
        { id: "chat", description: "Local chat" },
        { id: "completion", description: "Local completion" },
        { id: "*", description: "Fallback for any capability" },
      ],
      latencyMs: { min: 20, max: 50 },
    });
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      model: "local-instruct",
      mock: true,
      capability: request.capability,
      text: `[Local LLM mock] ${request.capability}`,
      input: request.input,
    };
  }
}

export class MockProvider extends BaseProvider {
  constructor() {
    super({
      id: "provider.mock",
      name: "Mock Provider",
      kind: "mock",
      baseUrl: "mock://ados",
      capabilities: [
        { id: "*", description: "Universal mock fallback" },
        { id: "chat", description: "Mock chat" },
        { id: "completion", description: "Mock completion" },
      ],
      latencyMs: { min: 10, max: 30 },
      notes: "Deterministic mock — no external network",
    });
  }

  protected mockExecute(request: ProviderExecuteRequest): unknown {
    return {
      provider: this.name,
      mock: true,
      capability: request.capability,
      text: `[Mock] ${request.capability}`,
      input: request.input,
    };
  }
}

export function createBuiltinProviders() {
  return [
    new CursorProvider(),
    new OpenAIProvider(),
    new ClaudeProvider(),
    new GitHubProvider(),
    new LocalLlmProvider(),
    new MockProvider(),
  ] as const;
}
