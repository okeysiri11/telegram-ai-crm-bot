import type { McpPromptDefinition } from "./types.js";

export function createBuiltinPrompts(): McpPromptDefinition[] {
  return [
    {
      name: "explain_module",
      description: "Explain an ADOS module",
      permission: "read",
      arguments: [
        { name: "module", description: "Module id or path", required: true },
      ],
      template:
        "Explain the ADOS module {{module}} in enterprise architecture terms: purpose, boundaries, dependencies, and how it integrates with Runtime.",
    },
    {
      name: "review_code",
      description: "Review code for ADOS standards",
      permission: "read",
      arguments: [
        { name: "path", description: "File or module path", required: true },
        { name: "focus", description: "Review focus", required: false },
      ],
      template:
        "Review code at {{path}} for ADOS enterprise architecture. Focus: {{focus}}. Check modularity, service boundaries, and Runtime compatibility.",
    },
    {
      name: "create_workflow",
      description: "Create a multi-agent workflow plan",
      permission: "execute",
      arguments: [
        { name: "goal", description: "Workflow goal", required: true },
      ],
      template:
        "Design an ADOS collaboration workflow for: {{goal}}. Include agents, steps, providers, and success criteria.",
    },
    {
      name: "generate_ui",
      description: "Generate Control Center UI guidance",
      permission: "execute",
      arguments: [
        { name: "page", description: "Page or feature name", required: true },
      ],
      template:
        "Generate UI guidance for ADOS Control Center page {{page}} using the existing design system and live Runtime data patterns.",
    },
    {
      name: "generate_documentation",
      description: "Generate documentation outline",
      permission: "read",
      arguments: [
        { name: "topic", description: "Documentation topic", required: true },
      ],
      template:
        "Write enterprise documentation for {{topic}} covering architecture, APIs, configuration, and operations.",
    },
    {
      name: "architecture_review",
      description: "Architecture review checklist",
      permission: "read",
      arguments: [
        { name: "scope", description: "Review scope", required: true },
      ],
      template:
        "Perform an ADOS architecture review for {{scope}}. Validate layering: Platform → Providers → AI → Business → Verticals.",
    },
    {
      name: "bug_investigation",
      description: "Bug investigation playbook",
      permission: "execute",
      arguments: [
        { name: "symptom", description: "Bug symptom", required: true },
      ],
      template:
        "Investigate ADOS bug: {{symptom}}. Use Runtime status, logs, agents, and providers. Propose root cause and fix path.",
    },
  ];
}

export class MCPPrompts {
  private readonly prompts = new Map<string, McpPromptDefinition>();

  constructor(initial?: readonly McpPromptDefinition[]) {
    for (const p of initial ?? createBuiltinPrompts()) {
      this.register(p);
    }
  }

  register(prompt: McpPromptDefinition): void {
    this.prompts.set(prompt.name, prompt);
  }

  get(name: string): McpPromptDefinition | undefined {
    return this.prompts.get(name);
  }

  list(): McpPromptDefinition[] {
    return [...this.prompts.values()];
  }

  render(
    name: string,
    args: Readonly<Record<string, string>>,
  ): { description: string; messages: Array<{ role: string; content: string }> } {
    const prompt = this.prompts.get(name);
    if (!prompt) throw new Error(`Unknown prompt: ${name}`);
    let text = prompt.template;
    for (const [k, v] of Object.entries(args)) {
      text = text.replaceAll(`{{${k}}}`, v);
    }
    text = text.replaceAll(/\{\{\w+\}\}/g, "");
    return {
      description: prompt.description,
      messages: [{ role: "user", content: text.trim() }],
    };
  }
}

export function createMCPPrompts(
  initial?: readonly McpPromptDefinition[],
): MCPPrompts {
  return new MCPPrompts(initial);
}
