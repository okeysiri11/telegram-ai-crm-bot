/**
 * Compact live Runtime Monitor — Sprint 28.1.
 * One subscription to Runtime Engine; reuse on Desktop / Dashboard / City / Production / CC.
 * Does not redesign surfaces — additive strip only.
 */

import { Badge } from "@/ui";
import { useRuntimeEngine } from "./useRuntimeEngine";
import type { HealthLevel } from "./types";

function toneFor(level: HealthLevel): "success" | "warning" | "danger" | "default" {
  if (level === "healthy") return "success";
  if (level === "warning") return "warning";
  if (level === "critical") return "danger";
  return "default";
}

/** Full-width glance for Command Center / Production / City headers. */
export function EnterpriseRuntimeMonitor() {
  const snap = useRuntimeEngine();
  const m = snap.metrics;
  return (
    <div className="row ert-monitor" style={{ gap: 8, flexWrap: "wrap", alignItems: "center" }} aria-label="Enterprise Runtime">
      <Badge tone={toneFor(snap.status)}>OS {snap.status}</Badge>
      <Badge>CPU {m.cpuPct}%</Badge>
      <Badge>Mem {m.memoryPct}%</Badge>
      <Badge>GPU {m.gpuPct}%</Badge>
      <Badge tone={m.jobsRunning ? "info" : "default"}>
        Jobs {m.jobsRunning}/{m.jobsWaiting}
      </Badge>
      <Badge tone={m.agentsActive ? "info" : "default"}>Agents {m.agentsActive}</Badge>
      <Badge>
        Providers {m.providersOnline}/{m.providersTotal}
      </Badge>
      <Badge>Workers {m.workers}</Badge>
      <Badge>Sessions {m.sessions}</Badge>
      <Badge tone={m.queueGeneration ? "info" : "default"}>Gen {m.queueGeneration ?? 0}</Badge>
      <Badge tone={m.queueRender ? "info" : "default"}>Render {m.queueRender ?? 0}</Badge>
      <Badge tone={m.queuePublishing ? "info" : "default"}>Pub {m.queuePublishing ?? 0}</Badge>
      <span className="eds-type-helper" title={m.heartbeatAt}>
        tick {m.tick}
      </span>
    </div>
  );
}

/** Menubar / dock-scale chips — Desktop & strips. */
export function EnterpriseRuntimeMonitorCompact() {
  const snap = useRuntimeEngine();
  const m = snap.metrics;
  return (
    <span className="edt-status-chip ert-compact" title={`Heartbeat ${m.heartbeatAt}`} aria-label="Runtime metrics">
      <span className={`ews-dot ews-dot--${snap.status === "healthy" ? "ok" : snap.status === "critical" ? "err" : "warn"}`} aria-hidden />
      CPU {m.cpuPct}% · Jobs {m.jobsRunning} · AI {m.agentsActive}
    </span>
  );
}
