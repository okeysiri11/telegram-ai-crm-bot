/**
 * Production Runtime Monitor panel — Sprint 28.2.
 * Uses existing Design System + Runtime Engine. Lazy-loaded from Production Center.
 */

import { useEffect, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { productionRuntime } from "./productionRuntime";
import { UNIVERSAL_PIPELINES } from "./universalPipelines";
import { useJobManager, useRuntimeEngine } from "./useRuntimeEngine";
import type { ProductionQueueKind, UniversalPipelineId } from "./types";

const QUEUE_LABELS: Record<ProductionQueueKind, string> = {
  production: "Production",
  task: "Task",
  render: "Render",
  generation: "Generation",
  publishing: "Publishing",
};

export function ProductionRuntimePanel() {
  const snap = useRuntimeEngine();
  const { jobs } = useJobManager();
  const [tick, setTick] = useState(0);

  useEffect(() => productionRuntime.subscribe(() => setTick((t) => t + 1)), []);

  const monitor = productionRuntime.monitor();
  void tick;

  const prodJobs = jobs.filter((j) => j.queueKind || j.source === "production");

  return (
    <div className="stack-md" aria-label="Production Runtime">
      <Card title="Production Runtime · Queues">
        <p className="eds-type-helper mb-3">
          Backed by Enterprise Runtime Engine · Job Manager · Health {snap.status} · tick {snap.metrics.tick}
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {(Object.keys(QUEUE_LABELS) as ProductionQueueKind[]).map((q) => {
            const row = monitor.queues[q];
            return (
              <div key={q} className="ews-glass" style={{ padding: 12, borderRadius: "var(--eds-radius-xl)" }}>
                <p className="eds-type-caption">{QUEUE_LABELS[q]} Queue</p>
                <p className="text-xl font-semibold">{row.length}</p>
                <p className="eds-type-helper">
                  run {row.running} · fail {row.failed} · ETA {row.etaSec || "—"}s
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Universal Pipelines">
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          {UNIVERSAL_PIPELINES.map((p) => (
            <Button
              key={p.id}
              size="sm"
              variant="secondary"
              onClick={() => productionRuntime.runUniversalPipeline(p.id as UniversalPipelineId)}
            >
              Run {p.label}
            </Button>
          ))}
        </div>
        <p className="eds-type-helper mt-2">
          Agent assignment · collaboration · multi-agent jobs via existing AI Agent Runtime.
        </p>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Background Workers">
          <ul className="stack-sm">
            {monitor.workers.map((w) => (
              <li key={w.id} className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                <span className="eds-type-small">
                  {w.label} · {QUEUE_LABELS[w.queueKind]}
                </span>
                <Badge tone={w.status === "busy" ? "info" : w.status === "offline" ? "danger" : "success"}>
                  {w.status} · load {w.load}/{w.capacity}
                </Badge>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Queue Analytics">
          <p className="eds-type-small">
            Throughput/tick: <strong>{monitor.analytics.throughputPerTick}</strong>
          </p>
          <p className="eds-type-small">
            Retry rate: <strong>{(monitor.analytics.retryRate * 100).toFixed(0)}%</strong>
          </p>
          <p className="eds-type-small">
            Workers busy: <strong>
              {monitor.analytics.workersBusy}/{monitor.analytics.workersTotal}
            </strong>
          </p>
          <p className="eds-type-small">
            Est. clear: <strong>{monitor.analytics.estimatedClearSec}s</strong>
          </p>
          <div className="row mt-3" style={{ gap: 8 }}>
            <Button size="sm" variant="secondary" onClick={() => productionRuntime.retryFailed()}>
              Retry failed
            </Button>
          </div>
        </Card>
      </div>

      <Card title="Job / Progress Monitor">
        <ul className="stack-sm">
          {prodJobs.slice(0, 16).map((j) => (
            <li key={j.id} className="row" style={{ justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
              <div>
                <p className="eds-type-small font-medium">{j.title}</p>
                <p className="eds-type-helper">
                  {j.queueKind || j.source} · {j.status} · {j.progress}%
                  {j.etaSec != null ? ` · ETA ${j.etaSec}s` : ""}
                  {j.workerId ? ` · ${j.workerId}` : ""}
                </p>
              </div>
              <div className="row" style={{ gap: 6 }}>
                {j.status === "failed" ? (
                  <Button size="sm" variant="ghost" onClick={() => productionRuntime.retryFailed(1)}>
                    Retry
                  </Button>
                ) : null}
                {j.status === "running" || j.status === "waiting" || j.status === "retrying" ? (
                  <Button size="sm" variant="ghost" onClick={() => productionRuntime.cancel(j.id)}>
                    Cancel
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
