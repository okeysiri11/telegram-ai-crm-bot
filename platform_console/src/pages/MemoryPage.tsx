import { useQuery } from "@tanstack/react-query";
import { runtimeApi } from "../services/runtimeApi";

export function MemoryPage() {
  const memories = useQuery({
    queryKey: ["runtime", "memory"],
    queryFn: async () => (await runtimeApi.memoryList()).memories,
    refetchInterval: 2000,
  });

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Shared Memory</h1>
      <p className="text-sm text-[var(--muted)]">
        Enterprise shared context per collaboration workflow
      </p>
      <div className="space-y-3">
        {(memories.data ?? []).map((m) => (
          <MemoryCard key={m.workflowId} id={m.workflowId} meta={m} />
        ))}
        {!memories.data?.length && (
          <div className="glass rounded-2xl p-6 text-sm text-[var(--muted)]">
            No shared contexts yet. Start a collaboration workflow.
          </div>
        )}
      </div>
    </div>
  );
}

function MemoryCard({
  id,
  meta,
}: {
  id: string;
  meta: {
    workflowId: string;
    templateId: string;
    status: string;
    contextKeys: string[];
    artifactCount: number;
  };
}) {
  const detail = useQuery({
    queryKey: ["runtime", "memory", id],
    queryFn: () => runtimeApi.memory(id),
    refetchInterval: 2000,
  });

  return (
    <div className="glass rounded-2xl p-5">
      <div className="font-medium">
        {meta.templateId} · {meta.status}
      </div>
      <div className="font-mono text-xs text-[var(--muted)]">{id}</div>
      <div className="mt-2 text-xs text-[var(--muted)]">
        keys: {meta.contextKeys.join(", ") || "—"} · artifacts: {meta.artifactCount}
      </div>
      <pre className="mt-3 max-h-48 overflow-auto text-xs text-[var(--muted)]">
        {JSON.stringify(detail.data ?? {}, null, 2)}
      </pre>
    </div>
  );
}
