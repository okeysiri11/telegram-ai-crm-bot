import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

export function WorkflowsPage() {
  const { workflows, socket } = useRuntime();
  const qc = useQueryClient();
  const invalidate = () => void qc.invalidateQueries({ queryKey: ["runtime"] });

  const templates = useQuery({
    queryKey: ["runtime", "workflow-templates"],
    queryFn: async () => (await runtimeApi.workflowTemplates()).templates,
    refetchInterval: 5000,
  });

  const overview = useQuery({
    queryKey: ["runtime", "collab-overview"],
    queryFn: runtimeApi.collaborationOverview,
    refetchInterval: 2000,
  });

  const start = useMutation({
    mutationFn: (templateId: string) =>
      runtimeApi.startCollaboration({
        templateId,
        name: templateId === "tpl.crm_generation" ? "CRM for construction company" : undefined,
        payload: { source: "control-center" },
      }),
    onSuccess: invalidate,
  });

  const pause = useMutation({
    mutationFn: (id: string) => runtimeApi.pauseCollaboration(id),
    onSuccess: invalidate,
  });
  const resume = useMutation({
    mutationFn: (id: string) => runtimeApi.resumeCollaboration(id),
    onSuccess: invalidate,
  });
  const cancel = useMutation({
    mutationFn: (id: string) => runtimeApi.cancelCollaboration(id),
    onSuccess: invalidate,
  });

  const collab = workflows.data?.collaboration ?? [];
  const defs = workflows.data?.workflows ?? [];
  const ov = overview.data;

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-semibold">Workflows</h1>
        <p className="text-sm text-[var(--muted)]">
          Multi-agent collaboration · WS {socket.status}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat title="Running" value={String(ov?.running ?? 0)} />
        <Stat title="Completed" value={String(ov?.completed ?? 0)} />
        <Stat title="Failed" value={String(ov?.failed ?? 0)} />
        <Stat title="Success Rate" value={`${ov?.successRate ?? 100}%`} />
      </div>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-4 text-sm uppercase tracking-widest text-[var(--muted)]">
          Workflow Templates
        </h2>
        <div className="grid gap-3 md:grid-cols-2">
          {(templates.data ?? []).map((t) => (
            <div
              key={t.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-[var(--border)] px-4 py-3"
            >
              <div>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-[var(--muted)]">
                  {t.description} · ~{t.estimatedMs}ms · {t.steps.length} steps
                </div>
              </div>
              <button
                type="button"
                className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200"
                onClick={() => start.mutate(t.id)}
              >
                Start
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-4 text-sm uppercase tracking-widest text-[var(--muted)]">
          Collaboration Runs
        </h2>
        <div className="space-y-3">
          {collab.map((w) => (
            <div key={w.id} className="rounded-xl border border-[var(--border)] p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium">
                    {w.name}{" "}
                    <span className="text-xs text-[var(--muted)]">({w.status})</span>
                  </div>
                  <div className="font-mono text-xs text-[var(--muted)]">{w.id}</div>
                </div>
                <div className="flex gap-2">
                  <button type="button" className="rounded border border-[var(--border)] px-2 py-1 text-xs" onClick={() => pause.mutate(w.id)}>Pause</button>
                  <button type="button" className="rounded border border-[var(--border)] px-2 py-1 text-xs" onClick={() => resume.mutate(w.id)}>Resume</button>
                  <button type="button" className="rounded border border-[var(--border)] px-2 py-1 text-xs" onClick={() => cancel.mutate(w.id)}>Cancel</button>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {w.steps.map((s) => (
                  <span
                    key={s.id}
                    className="rounded-lg border border-[var(--border)] px-2 py-1 text-xs"
                  >
                    {s.id}: {s.status}
                  </span>
                ))}
              </div>
              <div className="mt-2 text-xs text-[var(--muted)]">
                Graph: {w.graph.nodes.map((n) => n.label).join(" → ")} · elapsed{" "}
                {w.elapsedMs}ms / est {w.estimatedMs}ms
              </div>
            </div>
          ))}
          {!collab.length && (
            <p className="text-sm text-[var(--muted)]">No collaboration runs yet. Start a template.</p>
          )}
        </div>
      </section>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">
          Kernel Workflow Definitions
        </h2>
        <ul className="space-y-2 text-sm">
          {defs.map((w) => (
            <li key={w.id} className="rounded-lg border border-[var(--border)] px-3 py-2">
              {w.name} ({w.id}) · {w.steps} steps
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)]">{title}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
