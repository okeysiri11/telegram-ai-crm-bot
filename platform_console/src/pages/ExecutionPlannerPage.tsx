import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

const DEFAULT_SPEC = `{
  "mission": "Ship Execution Planner",
  "objective": "Execute ChatGPT engineering specifications",
  "requirements": ["Analyze spec", "Split agent work", "Parallel execution"],
  "files": ["src/execution/ExecutionPlanner.ts", "platform_console/src/pages/ExecutionPlannerPage.tsx"],
  "modules": ["src/execution", "platform_console"],
  "tests": ["unit", "integration"],
  "acceptanceCriteria": ["Plan API works", "Report includes build/test status"]
}`;

export function ExecutionPlannerPage() {
  const { status, socket } = useRuntime();
  const qc = useQueryClient();
  const [specText, setSpecText] = useState(DEFAULT_SPEC);

  const execStatus = useQuery({
    queryKey: ["runtime", "execution-status"],
    queryFn: runtimeApi.executionStatus,
    refetchInterval: 2000,
  });
  const history = useQuery({
    queryKey: ["runtime", "execution-history"],
    queryFn: () => runtimeApi.executionHistory(20),
    refetchInterval: 4000,
  });
  const report = useQuery({
    queryKey: ["runtime", "execution-report"],
    queryFn: runtimeApi.executionReport,
    refetchInterval: 4000,
    retry: false,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["runtime"] });
  };

  const runPlan = useMutation({
    mutationFn: async () => {
      const specification = JSON.parse(specText) as Record<string, unknown>;
      return runtimeApi.executionPlan({ specification, autoRun: true });
    },
    onSuccess: invalidate,
  });

  const st = execStatus.data;
  const plan = st?.currentPlan;
  const graph = plan?.graph;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Execution Planner</h1>
          <p className="text-sm text-[var(--muted)]">
            ChatGPT specs → Orchestrator · WS {socket.status} · module{" "}
            {status.data?.execution ?? "…"}
          </p>
        </div>
        <button
          type="button"
          className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
          disabled={runPlan.isPending}
          onClick={() => runPlan.mutate()}
        >
          {runPlan.isPending ? "Running…" : "Create & run plan"}
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Plan Status" value={plan?.status ?? "idle"} />
        <Card title="Progress" value={`${plan?.progress ?? 0}%`} />
        <Card
          title="Running Agents"
          value={(st?.runningAgents ?? []).join(", ") || "—"}
        />
        <Card
          title="Blocked"
          value={String(st?.blockedTasks?.length ?? plan?.blockedCount ?? 0)}
        />
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-2 text-sm font-medium">Engineering Specification</h2>
        <textarea
          className="min-h-40 w-full rounded-xl border border-[var(--border)] bg-black/20 p-3 font-mono text-xs outline-none focus:border-sky-500/50"
          value={specText}
          onChange={(e) => setSpecText(e.target.value)}
        />
        {runPlan.isError && (
          <p className="mt-2 text-xs text-rose-300">
            {(runPlan.error as Error)?.message ?? "Failed"}
          </p>
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Current Plan / Tasks</h2>
          <ul className="max-h-72 space-y-2 overflow-y-auto text-xs">
            {(plan?.tasks ?? []).map((t) => (
              <li
                key={t.id}
                className="rounded-xl border border-[var(--border)]/60 bg-black/10 p-2"
              >
                <div className="flex justify-between gap-2">
                  <span className="font-medium">{t.title}</span>
                  <span className="text-[var(--muted)]">{t.status}</span>
                </div>
                <div className="text-[var(--muted)]">
                  {t.role} → {t.agentId} · {t.progress}%
                </div>
              </li>
            ))}
            {!plan?.tasks?.length && (
              <li className="text-[var(--muted)]">No active plan</li>
            )}
          </ul>
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Execution Graph</h2>
          <div className="mb-3 flex flex-wrap gap-2 text-[10px]">
            {(graph?.nodes ?? []).map((n) => (
              <span
                key={n.id}
                className="rounded-lg border border-[var(--border)] px-2 py-1"
              >
                {n.role}:{n.status}
              </span>
            ))}
          </div>
          <ul className="max-h-40 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
            {(graph?.edges ?? []).map((e, i) => (
              <li key={`${e.from}-${e.to}-${i}`}>
                {e.from} → {e.to}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Report</h2>
          <p className="text-sm">
            {report.data?.report.summary ??
              st?.lastReport?.summary ??
              "No report yet"}
          </p>
          <dl className="mt-3 space-y-1 text-xs text-[var(--muted)]">
            <div>
              Build: {report.data?.report.buildStatus ?? st?.lastReport?.buildStatus ?? "—"}
            </div>
            <div>
              Tests: {report.data?.report.testStatus ?? st?.lastReport?.testStatus ?? "—"}
            </div>
            <div>
              Completed:{" "}
              {(report.data?.report.completedTasks ?? st?.lastReport?.completedTasks ?? []).length}
            </div>
            <div>
              Failed:{" "}
              {(report.data?.report.failedTasks ?? st?.lastReport?.failedTasks ?? []).length}
            </div>
          </dl>
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Logs</h2>
          <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
            {(st?.logs ?? []).slice(-40).map((line, i) => (
              <li key={`${i}-${line.slice(0, 12)}`}>{line}</li>
            ))}
          </ul>
        </section>
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-3 text-sm font-medium">History</h2>
        <ul className="max-h-40 space-y-1 overflow-y-auto text-xs">
          {(history.data?.history ?? []).map((h) => (
            <li key={h.id} className="border-b border-[var(--border)]/40 py-1">
              {h.planId} · {h.status} · {h.progress}%
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="glass rounded-2xl border border-[var(--border)] p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
        {title}
      </div>
      <div className="mt-1 truncate text-lg font-semibold">{value}</div>
    </div>
  );
}
