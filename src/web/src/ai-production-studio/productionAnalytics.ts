/**
 * Sprint 32.0 — Production analytics for Owner + Studio dashboards.
 * Reads productionStore snapshot + jobManager — no second analytics engine.
 */

import { jobManager } from "@/enterprise-runtime/jobManager";
import { productionRuntime } from "@/enterprise-runtime/productionRuntime";
import { estimateCostUsd, aiFailoverChain } from "@/enterprise-integrations/providerRegistry";
import type { AutomationJob, GenerationRecord, CreativePrompt, ProductionPipeline } from "./productionCatalog";
import { readBrandKit } from "./brandKit";

export type ProductionOwnerStats = {
  totalGenerations: number;
  completed: number;
  failed: number;
  running: number;
  queued: number;
  providerUsage: { providerId: string; title: string; jobs: number; costUsd: number }[];
  queueStatus: { generation: number; render: number; task: number; production: number };
  costTotalUsd: number;
  tokensTotal: number;
  topTemplates: { id: string; title: string; uses: number }[];
  topAgents: { name: string; uses: number }[];
  brand: string;
};

export function deriveProductionOwnerStats(input: {
  generations: GenerationRecord[];
  prompts: CreativePrompt[];
  jobs: AutomationJob[];
  pipelines: ProductionPipeline[];
}): ProductionOwnerStats {
  const gens = input.generations;
  const completed = gens.filter((g) => g.status === "done").length;
  const failed = gens.filter((g) => g.status === "failed").length;
  const running = gens.filter((g) => g.status === "running").length;
  const queued = gens.filter((g) => g.status === "queued").length;

  const counts = jobManager.counts();
  const mon = productionRuntime.monitor();
  const chain = aiFailoverChain();
  const brand = readBrandKit();

  const providerUsage = brand.defaultProviders.map((id) => {
    const meta = chain.find((p) => p.id === id);
    const jobs = gens.filter((g) => (g.providerId || brand.defaultProviders[0]) === id).length;
    const costUsd = gens
      .filter((g) => (g.providerId || brand.defaultProviders[0]) === id)
      .reduce((sum, g) => sum + (g.costUsd ?? 0), 0);
    return {
      providerId: id,
      title: meta?.title || id,
      jobs,
      costUsd: Number(costUsd.toFixed(4)),
    };
  });

  const promptUses = new Map<string, number>();
  for (const g of gens) {
    if (!g.promptId) continue;
    promptUses.set(g.promptId, (promptUses.get(g.promptId) || 0) + 1);
  }
  const topTemplates = [...promptUses.entries()]
    .map(([id, uses]) => ({
      id,
      title: input.prompts.find((p) => p.id === id)?.title || id,
      uses,
    }))
    .sort((a, b) => b.uses - a.uses)
    .slice(0, 5);

  const agentUses = new Map<string, number>();
  for (const g of gens) {
    for (const a of g.agents) agentUses.set(a, (agentUses.get(a) || 0) + 1);
  }
  const topAgents = [...agentUses.entries()]
    .map(([name, uses]) => ({ name, uses }))
    .sort((a, b) => b.uses - a.uses)
    .slice(0, 5);

  const costTotalUsd = gens.reduce((s, g) => s + (g.costUsd ?? 0), 0);
  const tokensTotal = gens.reduce((s, g) => s + (g.tokens ?? 0), 0);

  return {
    totalGenerations: gens.length,
    completed,
    failed,
    running: running + (counts.running || 0),
    queued: queued + (counts.waiting || 0) + input.jobs.filter((j) => j.status === "queued").length,
    providerUsage,
    queueStatus: {
      generation: mon.queues.generation?.length ?? 0,
      render: mon.queues.render?.length ?? 0,
      task: mon.queues.task?.length ?? 0,
      production: mon.queues.production?.length ?? 0,
    },
    costTotalUsd: Number(costTotalUsd.toFixed(4)),
    tokensTotal,
    topTemplates,
    topAgents,
    brand: brand.name,
  };
}

/** Estimate tokens/cost for a generation attempt (presentation over APH). */
export function estimateGenerationMeter(providerId: string, promptLen: number) {
  const tokens = Math.max(200, Math.round(promptLen / 3) + 800);
  const costUsd = estimateCostUsd(providerId, tokens);
  return { tokens, costUsd: Number(costUsd.toFixed(4)) };
}
