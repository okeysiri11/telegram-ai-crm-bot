/**
 * Cross-runtime consolidation map — Sprint 32.3.
 * Enterprise Runtime is the web orchestration hub; other runtimes are adapters/consumers.
 * Do not invent a parallel orchestrator.
 */

export type RuntimeLayerId =
  | "enterprise"
  | "ai"
  | "workflow"
  | "production"
  | "command"
  | "kernel_web"
  | "orchestrator_web";

export type RuntimeLayer = {
  id: RuntimeLayerId;
  role: "canonical" | "adapter" | "ui" | "presentation";
  path: string;
  owns: string[];
  mustNot: string[];
};

/** Single map — one responsibility per layer. */
export const RUNTIME_LAYERS: readonly RuntimeLayer[] = [
  {
    id: "enterprise",
    role: "canonical",
    path: "src/web/src/enterprise-runtime",
    owns: ["jobManager", "aiAgentRuntime", "agentOs", "productionRuntime", "healthService"],
    mustNot: ["second job queue SoR", "second agent registry"],
  },
  {
    id: "ai",
    role: "ui",
    path: "src/web/src/ai-runtime",
    owns: ["Agent Center pages", "strips"],
    mustNot: ["duplicate agent lifecycle"],
  },
  {
    id: "workflow",
    role: "adapter",
    path: "src/web/src/runtime/workflowRuntime",
    owns: ["client-side workflow graph UX"],
    mustNot: ["backend workflow SoR (use platform_workflow)"],
  },
  {
    id: "production",
    role: "adapter",
    path: "src/web/src/enterprise-runtime/productionRuntime.ts",
    owns: ["production queue analytics"],
    mustNot: ["parallel jobManager"],
  },
  {
    id: "command",
    role: "presentation",
    path: "src/web/src/runtime/commandRuntime",
    owns: ["command dispatch UX"],
    mustNot: ["platform event bus SoR"],
  },
  {
    id: "kernel_web",
    role: "presentation",
    path: "src/web/src/runtime/kernel",
    owns: ["bootstrap shell (≠ @ados/kernel)"],
    mustNot: ["rename collision with src/kernel"],
  },
  {
    id: "orchestrator_web",
    role: "presentation",
    path: "src/web/src/runtime/orchestrator",
    owns: ["frontend coordination (≠ @ados/orchestrator)"],
    mustNot: ["duplicate agentOs / jobManager"],
  },
] as const;

export function canonicalRuntimeLayer(): RuntimeLayer {
  return RUNTIME_LAYERS.find((l) => l.id === "enterprise")!;
}

export function runtimeConsolidationSummary(): {
  canonical: string;
  layers: number;
  sprint: string;
  principle: string;
} {
  return {
    canonical: canonicalRuntimeLayer().path,
    layers: RUNTIME_LAYERS.length,
    sprint: "32.3",
    principle: "enterprise_runtime_is_web_orchestration_hub",
  };
}
