/**
 * Sprint 30.5 — Owner AI dashboard (God Mode for AI tasks).
 */

import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { taskExecution, lifecycleLabelRu } from "./taskExecution";
import type { AiTaskSecurityContext } from "./aiTaskSecurity";
import type { JobPriority } from "@/enterprise-runtime/types";

export function OwnerAiDashboard({
  ctx,
  onChanged,
}: {
  ctx: AiTaskSecurityContext;
  onChanged?: () => void;
}) {
  const [msg, setMsg] = useState<string | null>(null);
  const jobs = useMemo(() => taskExecution.list(ctx), [ctx]);
  const dash = useMemo(() => taskExecution.dashboard(ctx), [ctx, jobs]);
  const running = jobs.filter(
    (j) => j.status === "running" || j.status === "paused" || j.status === "retrying" || j.status === "waiting",
  );

  async function act(label: string, fn: () => Promise<unknown>) {
    try {
      await fn();
      setMsg(label);
      onChanged?.();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Ошибка");
    }
  }

  return (
    <Card
      title="Owner Mode · AI"
      className="ec-owner-panel"
      status={<Badge tone="success">God Mode</Badge>}
      aria-label="Owner AI Dashboard"
    >
      <div className="ec-owner-grid">
        <div>
          <p className="eds-type-caption">Активные задачи</p>
          <p className="font-semibold">{running.length}</p>
        </div>
        <div>
          <p className="eds-type-caption">Ресурсы</p>
          <p className="eds-type-small">
            CPU {dash.cpuUsage}% · GPU {dash.gpuUsage}%
          </p>
        </div>
        <div>
          <p className="eds-type-caption">Успех / очередь</p>
          <p className="eds-type-small">
            {dash.successRate}% · Q {dash.queueLength}
          </p>
        </div>
      </div>

      <ul className="mt-3 space-y-2">
        {running.slice(0, 12).map((j) => (
          <li key={j.id} className="row" style={{ gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span className="eds-type-small flex-1 min-w-[12rem]">
              <strong>{j.title}</strong> · {lifecycleLabelRu(j.status)} · {j.progress}%
            </span>
            <Button size="sm" variant="ghost" onClick={() => void act("Force stop", () => taskExecution.forceStop(ctx, j.id))}>
              Стоп
            </Button>
            <Button size="sm" variant="ghost" onClick={() => void act("Restart", () => taskExecution.retry(ctx, j.id).then(() => taskExecution.start(ctx, j.id)))}>
              Рестарт
            </Button>
            {(["critical", "high", "normal", "low"] as JobPriority[]).map((p) => (
              <Button
                key={p}
                size="sm"
                variant={j.priority === p ? "primary" : "ghost"}
                onClick={() => void act(`Priority ${p}`, () => taskExecution.setPriority(ctx, j.id, p))}
              >
                {p}
              </Button>
            ))}
            <details className="eds-type-small">
              <summary>Логи</summary>
              <ul>
                {(j.logs || []).slice(-5).map((l, i) => (
                  <li key={`${j.id}_${i}`}>{l.message}</li>
                ))}
              </ul>
            </details>
          </li>
        ))}
        {!running.length ? <li className="eds-type-helper">Нет задач в работе</li> : null}
      </ul>
      {msg ? <p className="eds-type-helper mt-2">{msg}</p> : null}
    </Card>
  );
}
