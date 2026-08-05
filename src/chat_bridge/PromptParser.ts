import type { ChatTaskKind, ChatPriority, ParsedPrompt } from "./types.js";

const KIND_PATTERNS: Array<{ kind: ChatTaskKind; re: RegExp; agent: string; priority: ChatPriority }> = [
  { kind: "architecture", re: /architect|system design|adr|boundary|module layout/i, agent: "agent.architect", priority: 8 },
  { kind: "bugfix", re: /bug|fix|error|crash|null.?ref|regress/i, agent: "agent.developer", priority: 9 },
  { kind: "refactor", re: /refactor|cleanup|restructure|rename|debt/i, agent: "agent.developer", priority: 5 },
  { kind: "testing", re: /\bqa\b|test suite|unit test|integration test|coverage/i, agent: "agent.qa", priority: 6 },
  { kind: "documentation", re: /document|readme|guide|docs?\b|changelog/i, agent: "agent.research", priority: 4 },
  { kind: "research", re: /research|investigate|analyze|compare|survey/i, agent: "agent.research", priority: 5 },
  { kind: "deployment", re: /deploy|release|ci\/?cd|pipeline|devops|publish/i, agent: "agent.automation", priority: 7 },
  { kind: "code", re: /implement|feature|build|code|create|add|write/i, agent: "agent.developer", priority: 7 },
];

/**
 * Converts free-form ChatGPT text into a structured task kind + agent hint.
 */
export class PromptParser {
  parse(prompt: string): ParsedPrompt {
    const text = prompt.trim();
    if (!text) {
      return {
        kind: "code",
        title: "Empty prompt",
        description: "",
        priority: 3,
        preferredAgent: "agent.developer",
        files: [],
        modules: [],
        confidence: 0,
      };
    }

    let matched = KIND_PATTERNS.find((p) => p.re.test(text));
    if (!matched) {
      matched = {
        kind: "code",
        re: /.*/,
        agent: "agent.developer",
        priority: 5,
      };
    }

    const files = extractPaths(text);
    const modules = extractModules(text, files);
    const title = deriveTitle(text, matched.kind);
    const confidence = matched.kind === "code" && !KIND_PATTERNS[7]!.re.test(text) ? 0.55 : 0.85;

    return {
      kind: matched.kind,
      title,
      description: text,
      priority: matched.priority,
      preferredAgent: matched.agent,
      files,
      modules,
      confidence,
    };
  }
}

function deriveTitle(text: string, kind: ChatTaskKind): string {
  const first = text.split(/[\n.]/)[0]?.trim() ?? text;
  const clipped = first.length > 80 ? `${first.slice(0, 77)}…` : first;
  return clipped || `${kind} task`;
}

function extractPaths(text: string): string[] {
  const matches = text.match(
    /(?:[\w.-]+\/)+[\w.-]+\.(?:ts|tsx|js|jsx|py|md|json|yml|yaml|css)/g,
  );
  return [...new Set(matches ?? [])].slice(0, 20);
}

function extractModules(text: string, files: string[]): string[] {
  const fromFiles = files
    .map((f) => f.split("/")[0])
    .filter((x): x is string => Boolean(x));
  const named = text.match(
    /\b(?:src\/[\w-]+|platform_console|orchestrator|providers|kernel|chat_bridge)\b/g,
  );
  return [...new Set([...(named ?? []), ...fromFiles])].slice(0, 12);
}

export function createPromptParser(): PromptParser {
  return new PromptParser();
}
