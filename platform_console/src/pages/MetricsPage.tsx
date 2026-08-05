import { useQuery } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

export function MetricsPage() {
  const { metrics, status, agents } = useRuntime();
  const overview = useQuery({
    queryKey: ["runtime", "collab-overview"],
    queryFn: runtimeApi.collaborationOverview,
    refetchInterval: 2000,
  });
  const providerMetrics = useQuery({
    queryKey: ["runtime", "providers"],
    queryFn: runtimeApi.providers,
    refetchInterval: 2000,
  });

  const m = metrics.data;
  const ov = overview.data;
  const pm = providerMetrics.data?.metrics;

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Metrics</h1>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Uptime" value={m ? `${m.uptimeSec}s` : "…"} />
        <Card title="Heap" value={m ? `${Math.round(m.memory.heapUsed / 1e6)} MB` : "…"} />
        <Card title="CPU delta" value={m ? `${((m.cpu.userMicros + m.cpu.systemMicros) / 1000).toFixed(1)} ms` : "…"} />
        <Card title="System" value={status.data?.systemStatus ?? "…"} />
        <Card title="Workflows" value={String(ov?.workflows ?? 0)} />
        <Card title="Queue Size" value={String(ov?.queueSize ?? 0)} />
        <Card title="Avg Response" value={`${ov?.avgResponseTimeMs ?? 0} ms`} />
        <Card title="Success Rate" value={`${ov?.successRate ?? 100}%`} />
        <Card title="Provider Requests" value={String(pm?.totalRequests ?? 0)} />
        <Card title="Provider Latency" value={`${pm?.avgResponseTimeMs ?? 0} ms`} />
        <Card title="Provider Errors" value={String(pm?.errors ?? 0)} />
        <Card title="Agents" value={String(agents.data?.length ?? 0)} />
      </div>
    </div>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)]">{title}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
