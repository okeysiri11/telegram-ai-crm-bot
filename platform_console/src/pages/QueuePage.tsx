import { useQuery } from "@tanstack/react-query";
import { runtimeApi } from "../services/runtimeApi";

export function QueuePage() {
  const queue = useQuery({
    queryKey: ["runtime", "queue"],
    queryFn: runtimeApi.queue,
    refetchInterval: 2000,
  });

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Agent Queues</h1>
      <p className="text-sm text-[var(--muted)]">
        Total queued: {queue.data?.totalQueued ?? 0}
      </p>
      <div className="glass overflow-x-auto rounded-2xl">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-[var(--border)] text-xs uppercase tracking-widest text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3">Agent</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Queue</th>
              <th className="px-4 py-3">Running</th>
              <th className="px-4 py-3">Avg Response</th>
            </tr>
          </thead>
          <tbody>
            {(queue.data?.queues ?? []).map((q) => (
              <tr key={q.agentId} className="border-b border-[var(--border)]/40">
                <td className="px-4 py-3">{q.name}</td>
                <td className="px-4 py-3">{q.status}</td>
                <td className="px-4 py-3">{q.queueLength}</td>
                <td className="px-4 py-3 font-mono text-xs">{q.runningTask ?? "—"}</td>
                <td className="px-4 py-3">{q.avgResponseMs} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
