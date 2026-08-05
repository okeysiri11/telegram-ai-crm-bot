/**
 * Sprint 32.0 — AI / Render task queues with cost · tokens · logs.
 */

import { Badge, Button, Card } from "@/ui";
import { jobManager } from "@/enterprise-runtime/jobManager";
import { productionRuntime } from "@/enterprise-runtime/productionRuntime";
import { useProductionStore } from "./productionStore";
import { deriveProductionOwnerStats } from "./productionAnalytics";
import { useMemo, useState } from "react";

export function TaskQueuePanel() {
  const generations = useProductionStore((s) => s.generations);
  const prompts = useProductionStore((s) => s.prompts);
  const jobs = useProductionStore((s) => s.jobs);
  const pipelines = useProductionStore((s) => s.pipelines);
  const retryJob = useProductionStore((s) => s.retryJob);
  const settleGeneration = useProductionStore((s) => s.settleGeneration);
  const [, tick] = useState(0);

  const stats = useMemo(
    () => deriveProductionOwnerStats({ generations, prompts, jobs, pipelines }),
    [generations, prompts, jobs, pipelines],
  );
  const runtimeJobs = jobManager.list().filter((j) => j.source === "production" || j.queueKind);
  const mon = productionRuntime.monitor();

  return (
    <div className="space-y-3" data-testid="task-queue-panel">
      <div className="eds-grid eds-grid--dashboard">
        <Card title="AI Queue">
          <Badge tone="info">{stats.queueStatus.generation} gen</Badge>
          <p className="eds-type-helper mt-1">task {stats.queueStatus.task}</p>
        </Card>
        <Card title="Render Queue">
          <Badge>{stats.queueStatus.render}</Badge>
          <p className="eds-type-helper mt-1">eta {mon.queues.render?.etaSec ?? 0}s</p>
        </Card>
        <Card title="Cost">
          <p className="font-semibold">${stats.costTotalUsd}</p>
        </Card>
        <Card title="Tokens">
          <p className="font-semibold">{stats.tokensTotal}</p>
        </Card>
      </div>

      <Card title="Generation tasks" status={<Badge>{generations.length}</Badge>}>
        <ul className="space-y-2">
          {generations.slice(0, 12).map((g) => (
            <li key={g.id} className="rounded-md border border-[var(--ew-border)] px-3 py-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium eds-type-small">{g.title}</p>
                  <p className="eds-type-helper">
                    {g.status} · {g.providerId || "—"} · {g.tokens ?? 0} tok · $
                    {(g.costUsd ?? 0).toFixed(4)} · {g.durationMs ?? 0}ms
                  </p>
                </div>
                <div className="flex gap-1">
                  {g.status === "failed" ? (
                    <Button size="sm" variant="secondary" onClick={() => settleGeneration(g.id, "done")}>
                      Retry
                    </Button>
                  ) : null}
                  {g.status === "running" ? (
                    <Button size="sm" variant="ghost" onClick={() => settleGeneration(g.id, "done")}>
                      Force complete
                    </Button>
                  ) : null}
                </div>
              </div>
              {g.logs?.length ? (
                <ul className="mt-1 eds-type-caption text-[var(--eds-text-muted)]">
                  {g.logs.slice(-3).map((l, i) => (
                    <li key={`${g.id}_${i}`}>{l.message}</li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Runtime jobs" status={<Badge>{runtimeJobs.length}</Badge>}>
        <ul className="space-y-1 eds-type-small">
          {runtimeJobs.slice(0, 10).map((j) => (
            <li key={j.id}>
              {j.title} · {j.status} · {j.queueKind || "—"} · retries {j.retries}
            </li>
          ))}
          {!runtimeJobs.length ? <li className="eds-type-helper">Нет jobs</li> : null}
        </ul>
        <Button
          size="sm"
          className="mt-2"
          variant="ghost"
          onClick={() => {
            productionRuntime.retryFailed(8);
            jobs.filter((j) => j.status === "failed").forEach((j) => retryJob(j.id));
            tick((t) => t + 1);
          }}
        >
          Retry failed
        </Button>
      </Card>
    </div>
  );
}
