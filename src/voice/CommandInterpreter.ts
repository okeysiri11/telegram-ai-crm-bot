import type { ChatBridge } from "@ados/chat-bridge";
import type { VoiceCommand, VoiceIntent } from "./types.js";
import type { VoiceContext } from "./VoiceContext.js";
import type { IntentMatch } from "./IntentDetector.js";

export interface InterpretResult {
  readonly command: VoiceCommand;
  readonly navigation?: { path: string; label: string };
  readonly chatTaskId?: string;
  readonly executed: boolean;
  readonly responseText: string;
}

/**
 * Translates intents into ChatGPT Bridge tasks and/or Control Center navigation.
 */
export class CommandInterpreter {
  constructor(
    private readonly bridge: ChatBridge,
    private readonly context: VoiceContext,
  ) {}

  async interpret(
    command: VoiceCommand,
    match: IntentMatch,
    options: { autoExecute: boolean },
  ): Promise<InterpretResult> {
    command.intent = match.intent;
    command.confidence = match.confidence;
    command.entities = match.entities;
    command.status = "interpreted";

    this.context.update({ lastIntent: match.intent });
    this.context.appendUser(command.text);

    const nav = navigationFor(match.intent, match.entities);
    if (nav) {
      this.context.update({ currentPage: nav.path });
      if (match.intent === "open_module" && match.entities["module"]) {
        this.context.update({ selectedModule: match.entities["module"] });
      }
      const responseText = `Opening ${nav.label}.`;
      command.status = "completed";
      command.responseText = responseText;
      this.context.appendAssistant(responseText);
      return {
        command,
        navigation: nav,
        executed: true,
        responseText,
      };
    }

    const prompt = buildBridgePrompt(match.intent, command.text, match.entities);
    const agentHint = agentForIntent(match.intent);
    if (agentHint) {
      this.context.update({ selectedAgent: agentHint });
    }

    const task = this.bridge.createTask({
      prompt,
      autoRun: false,
      provider: this.context.get().currentProvider,
      projectContext: {
        project: this.context.get().currentProject,
        sprint: this.context.get().currentSprint,
        ...(this.context.get().selectedModule
          ? { affectedModules: [this.context.get().selectedModule!] }
          : {}),
      },
    });
    command.chatTaskId = task.id;
    command.status = "queued";

    let executed = false;
    let responseText = `Created task ${task.id} (${task.kind}) for ${match.intent.replace(/_/g, " ")}.`;

    if (options.autoExecute) {
      command.status = "executing";
      const done = await this.bridge.run(task.id);
      executed = true;
      command.status = done.status === "Failed" ? "failed" : "completed";
      if (done.status === "Failed") {
        command.error = done.error ?? "Execution failed";
        responseText = `Task failed: ${command.error}`;
      } else {
        responseText = `Completed via ${done.preferredAgent}. Generated ${done.generatedFiles.length} file(s).`;
      }
    }

    command.responseText = responseText;
    this.context.appendAssistant(responseText);
    const result: InterpretResult = {
      command,
      chatTaskId: task.id,
      executed,
      responseText,
    };
    return result;
  }
}

function navigationFor(
  intent: VoiceIntent,
  entities: Readonly<Record<string, string>>,
): { path: string; label: string } | undefined {
  switch (intent) {
    case "open_crm":
      return { path: "/crm", label: "CRM" };
    case "open_erp":
      return { path: "/erp", label: "ERP" };
    case "open_ai_studio":
      return { path: "/ai-studio", label: "AI Studio" };
    case "open_marketplace":
      return { path: "/marketplace", label: "Marketplace" };
    case "open_module": {
      const mod = entities["module"] ?? "module";
      const slug = mod.toLowerCase().replace(/\s+/g, "-");
      return { path: `/${slug}`, label: mod };
    }
    default:
      return undefined;
  }
}

function agentForIntent(intent: VoiceIntent): string | null {
  switch (intent) {
    case "generate_code":
    case "create_task":
    case "execute_command":
      return "agent.developer";
    case "review_code":
      return "agent.reviewer";
    case "explain_code":
    case "search":
      return "agent.research";
    case "create_document":
    case "generate_report":
      return "agent.research";
    case "run_workflow":
    case "run_agent":
      return "agent.automation";
    case "create_project":
      return "agent.architect";
    default:
      return null;
  }
}

function buildBridgePrompt(
  intent: VoiceIntent,
  text: string,
  entities: Readonly<Record<string, string>>,
): string {
  const entityLine = Object.entries(entities)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");
  switch (intent) {
    case "generate_code":
      return `Implement code${entities["topic"] ? ` for ${entities["topic"]}` : ""}: ${text}`;
    case "review_code":
      return `Review code${entities["target"] ? ` in ${entities["target"]}` : ""}: ${text}`;
    case "explain_code":
      return `Explain code${entities["target"] ? ` in ${entities["target"]}` : ""}: ${text}`;
    case "create_document":
      return `Write documentation${entities["topic"] ? ` about ${entities["topic"]}` : ""}: ${text}`;
    case "generate_report":
      return `Generate a report${entities["topic"] ? ` on ${entities["topic"]}` : ""}: ${text}`;
    case "create_task":
      return entities["task"] ?? text;
    case "create_project":
      return `Design architecture for project${entities["name"] ? ` ${entities["name"]}` : ""}: ${text}`;
    case "run_workflow":
      return `Run workflow${entities["workflow"] ? ` ${entities["workflow"]}` : ""}: ${text}`;
    case "run_agent":
      return `Run agent ${entities["agent"] ?? "developer"}${entities["task"] ? ` to ${entities["task"]}` : ""}: ${text}`;
    case "execute_command":
      return `Execute command: ${entities["command"] ?? text}`;
    case "search":
      return `Research and summarize: ${entities["query"] ?? text}`;
    default:
      return entityLine ? `${text} (${entityLine})` : text;
  }
}

export function createCommandInterpreter(
  bridge: ChatBridge,
  context: VoiceContext,
): CommandInterpreter {
  return new CommandInterpreter(bridge, context);
}
