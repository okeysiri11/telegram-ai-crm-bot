import { useQuery } from "@tanstack/react-query";
import { runtimeApi } from "../services/runtimeApi";

export function TimelinePage() {
  const timeline = useQuery({
    queryKey: ["runtime", "timeline"],
    queryFn: async () => (await runtimeApi.timeline()).events,
    refetchInterval: 2000,
  });

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Execution Timeline</h1>
      <div className="glass max-h-[75vh] overflow-auto rounded-2xl">
        {(timeline.data ?? []).map((e) => (
          <div key={e.id} className="border-b border-[var(--border)]/40 px-4 py-2 font-mono text-xs">
            <span className="text-[var(--muted)]">{e.at}</span>{" "}
            <span className="text-sky-200">{e.type}</span>{" "}
            {e.workflowId && <span>{e.workflowId} </span>}
            {e.agentId && <span className="text-[var(--ok)]">{e.agentId} </span>}
            {e.durationMs != null && <span>{e.durationMs}ms </span>}
            {e.message ?? e.error ?? ""}
          </div>
        ))}
        {!timeline.data?.length && (
          <p className="p-4 text-sm text-[var(--muted)]">No timeline events yet.</p>
        )}
      </div>
    </div>
  );
}
