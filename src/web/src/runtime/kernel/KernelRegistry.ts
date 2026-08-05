/**
 * Kernel registry — tracks kernel-visible platform modules (orchestration view).
 * Does not replace Orchestrator RuntimeRegistry.
 */

import { enterpriseOrchestrator } from "@/runtime/orchestrator";
import type { RuntimeId } from "@/runtime/orchestrator";

export type KernelModuleRecord = {
  id: string;
  kind: "kernel" | "orchestrator" | "runtime";
  label: string;
  version: string;
  loaded: boolean;
  status: string;
};

const extras = new Map<string, KernelModuleRecord>();

export const kernelRegistry = {
  clear() {
    extras.clear();
  },

  register(record: KernelModuleRecord) {
    extras.set(record.id, record);
    return record;
  },

  /** Snapshot of kernel + orchestrator-registered runtimes */
  list(): KernelModuleRecord[] {
    const out: KernelModuleRecord[] = [
      {
        id: "kernel",
        kind: "kernel",
        label: "Enterprise Kernel",
        version: "29.9",
        loaded: true,
        status: "healthy",
      },
      {
        id: "orchestrator",
        kind: "orchestrator",
        label: "Enterprise Orchestrator",
        version: enterpriseOrchestrator.isReady()
          ? enterpriseOrchestrator.version
          : "29.8",
        loaded: enterpriseOrchestrator.isReady(),
        status: enterpriseOrchestrator.isReady() ? "healthy" : "stopped",
      },
    ];

    if (enterpriseOrchestrator.isReady()) {
      for (const r of enterpriseOrchestrator.runtimes()) {
        out.push({
          id: r.id,
          kind: "runtime",
          label: r.label,
          version: r.version,
          loaded: r.status !== "stopped",
          status: r.status,
        });
      }
    }

    for (const e of extras.values()) out.push(e);
    return out;
  },

  get(id: string) {
    return this.list().find((m) => m.id === id);
  },

  runtimeIds(): RuntimeId[] {
    if (!enterpriseOrchestrator.isReady()) return [];
    return enterpriseOrchestrator.registry.ids();
  },
};
