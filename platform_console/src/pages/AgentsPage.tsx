import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi, type AgentDto } from "../services/runtimeApi";

function statusClass(status: string): string {
  if (status === "Idle" || status === "Ready") return "status-ok";
  if (status === "Running" || status === "Busy" || status === "Waiting") return "status-warn";
  return "status-err";
}

function avatar(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function AgentsPage() {
  const { agents, status, socket } = useRuntime();
  const qc = useQueryClient();
  const rows = agents.data ?? [];
  const orch = status.data;

  const overview = useQuery({
    queryKey: ["runtime", "collab-overview"],
    queryFn: runtimeApi.collaborationOverview,
    refetchInterval: 2000,
  });

  const agentLogs = useQuery({
    queryKey: ["runtime", "agent-logs"],
    queryFn: async () => (await runtimeApi.agentLogs()).logs,
    refetchInterval: 2000,
  });

  const runCrm = useMutation({
    mutationFn: () =>
      runtimeApi.startCollaboration({
        templateId: "tpl.crm_generation",
        name: "CRM for construction company",
        payload: { industry: "construction" },
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["runtime"] }),
  });

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">AI Agents</h1>
          <p className="text-sm text-[var(--muted)]">
            Multi-agent collaboration · WS {socket.status}
          </p>
        </div>
        <button
          type="button"
          onClick={() => runCrm.mutate()}
          className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
        >
          Run CRM workflow
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="AI Orchestrator" value={orch?.orchestrator ?? "…"} ok={orch?.orchestrator === "OK"} />
        <Metric title="Agents" value={String(rows.length)} />
        <Metric title="Queue" value={String(overview.data?.queueSize ?? 0)} />
        <Metric title="Success Rate" value={`${overview.data?.successRate ?? 100}%`} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((a: AgentDto) => (
          <div key={a.id} className="glass rounded-2xl p-4">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/20 text-sm font-semibold text-sky-200">
                {avatar(a.name ?? a.id)}
              </div>
              <div>
                <div className="font-medium">{a.name ?? a.id}</div>
                <div className="text-xs text-[var(--muted)]">
                  {a.role} · v{a.version ?? "3.0.0"}
                </div>
              </div>
              <span className={`ml-auto status-dot ${statusClass(a.status)}`} />
            </div>
            <div className="space-y-1 text-xs text-[var(--muted)]">
              <div>Status: <span className="text-white">{a.status}</span></div>
              <div>Provider: <span className="text-white">{a.provider}</span></div>
              <div>Current: <span className="text-white">{a.currentTask ?? "—"}</span></div>
              <div>Queue: <span className="text-white">{a.queueSize ?? 0}</span></div>
              <div>Response: <span className="text-white">{a.responseTimeMs ?? 0} ms</span></div>
              <div>Health: <span className="text-white">{a.health ?? "—"}</span></div>
              <div>Last: <span className="text-white">{a.lastExecution ?? "—"}</span></div>
              <div>Skills: {(a.skills ?? []).join(", ") || "—"}</div>
            </div>
          </div>
        ))}
      </div>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">Agent Logs</h2>
        <div className="max-h-64 overflow-auto font-mono text-xs">
          {(agentLogs.data ?? []).slice(0, 80).map((log) => (
            <div key={log.id} className="border-b border-[var(--border)]/40 py-1">
              <span className="text-[var(--muted)]">{log.at}</span>{" "}
              <span className="text-sky-200">{log.agentId}</span> {log.message}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Metric({ title, value, ok = true }: { title: string; value: string; ok?: boolean }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-widest text-[var(--muted)]">
        {title}
        <span className={`status-dot ${ok ? "status-ok" : "status-err"}`} />
      </div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}
