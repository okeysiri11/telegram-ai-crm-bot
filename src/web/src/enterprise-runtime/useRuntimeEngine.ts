/**
 * Runtime Engine React bindings — Sprint 28.1.
 */

import { useEffect, useState, useSyncExternalStore } from "react";
import { runtimeEngine } from "./runtimeEngine";
import { jobManager } from "./jobManager";
import { aiAgentRuntime } from "./aiAgentRuntime";
import type { AiAgentRuntime, RuntimeJobRecord, RuntimeSnapshot } from "./types";

function subscribeRuntime(cb: () => void) {
  return runtimeEngine.subscribe(() => cb());
}

function getRuntimeSnapshot() {
  return runtimeEngine.getSnapshot();
}

/** Full runtime snapshot (metrics · jobs · agents · health). */
export function useRuntimeEngine(): RuntimeSnapshot {
  return useSyncExternalStore(subscribeRuntime, getRuntimeSnapshot, getRuntimeSnapshot);
}

export function useJobManager(): {
  jobs: RuntimeJobRecord[];
  counts: ReturnType<typeof jobManager.counts>;
} {
  const [jobs, setJobs] = useState(() => jobManager.list());
  useEffect(() => {
    return jobManager.subscribe(setJobs);
  }, []);
  return { jobs, counts: jobManager.counts() };
}

export function useAiAgentRuntime(): AiAgentRuntime[] {
  const [agents, setAgents] = useState(() => aiAgentRuntime.list());
  useEffect(() => {
    return aiAgentRuntime.subscribe(setAgents);
  }, []);
  return agents;
}
