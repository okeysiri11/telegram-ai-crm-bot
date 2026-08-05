/**
 * Persistent runtime bar — Sprint 28.5.
 * Extends StatusBar presentation with Runtime Engine metrics.
 */

import { useRuntimeEngine } from "@/enterprise-runtime/useRuntimeEngine";
import { StatusBar } from "./StatusBar";

export function ShellRuntimeBar() {
  const snap = useRuntimeEngine();
  const m = snap.metrics;

  return (
    <div className="ews-runtime-bar" aria-label="Enterprise runtime bar">
      <div className="ews-runtime-metrics eds-type-helper" style={{ display: "flex", gap: 12, flexWrap: "wrap", padding: "0.25rem 0.75rem" }}>
        <span>CPU {m.cpuPct}%</span>
        <span>Mem {m.memoryPct}%</span>
        <span>Queue G{m.queueGeneration ?? 0}/R{m.queueRender ?? 0}</span>
        <span>Jobs {m.jobsRunning}/{m.jobsWaiting}</span>
        <span>AI {m.agentsActive}</span>
        <span>
          Providers {m.providersOnline}/{m.providersTotal}
        </span>
        <span>Workers {m.workers}</span>
        <span title={m.heartbeatAt}>tick {m.tick}</span>
      </div>
      <StatusBar />
    </div>
  );
}
