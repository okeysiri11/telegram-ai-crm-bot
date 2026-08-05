import { useQuery } from "@tanstack/react-query";
import { runtimeApi } from "../services/runtimeApi";

export function TasksPage() {
  const tasks = useQuery({
    queryKey: ["runtime", "tasks"],
    queryFn: runtimeApi.tasks,
    refetchInterval: 2000,
  });

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Tasks</h1>
      <div className="grid gap-4 lg:grid-cols-3">
        <TaskCol title="Running" rows={tasks.data?.running ?? []} />
        <TaskCol title="Completed" rows={tasks.data?.completed ?? []} />
        <TaskCol title="Failed" rows={tasks.data?.failed ?? []} />
      </div>
    </div>
  );
}

function TaskCol({
  title,
  rows,
}: {
  title: string;
  rows: Array<{
    workflowId: string;
    workflowName: string;
    stepId: string;
    agentId: string;
    status: string;
    durationMs?: number;
    error?: string;
  }>;
}) {
  return (
    <section className="glass rounded-2xl p-4">
      <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">
        {title} ({rows.length})
      </h2>
      <div className="max-h-96 space-y-2 overflow-auto text-xs">
        {rows.map((r, i) => (
          <div key={`${r.workflowId}-${r.stepId}-${i}`} className="rounded-lg border border-[var(--border)] p-2">
            <div className="font-medium">{r.workflowName} / {r.stepId}</div>
            <div className="text-[var(--muted)]">
              {r.agentId} · {r.status}
              {r.durationMs != null ? ` · ${r.durationMs}ms` : ""}
            </div>
            {r.error && <div className="text-[var(--err)]">{r.error}</div>}
          </div>
        ))}
        {!rows.length && <p className="text-[var(--muted)]">None</p>}
      </div>
    </section>
  );
}
