import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

export function McpGatewayPage() {
  const { status, socket } = useRuntime();
  const qc = useQueryClient();

  const mcpStatus = useQuery({
    queryKey: ["runtime", "mcp-status"],
    queryFn: runtimeApi.mcpStatus,
    refetchInterval: 2000,
  });
  const tools = useQuery({
    queryKey: ["runtime", "mcp-tools"],
    queryFn: runtimeApi.mcpTools,
    refetchInterval: 5000,
  });
  const resources = useQuery({
    queryKey: ["runtime", "mcp-resources"],
    queryFn: runtimeApi.mcpResources,
    refetchInterval: 5000,
  });
  const prompts = useQuery({
    queryKey: ["runtime", "mcp-prompts"],
    queryFn: runtimeApi.mcpPrompts,
    refetchInterval: 5000,
  });

  const connect = useMutation({
    mutationFn: () => runtimeApi.mcpConnect("control-center"),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["runtime"] }),
  });

  const st = mcpStatus.data;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">MCP Gateway</h1>
          <p className="text-sm text-[var(--muted)]">
            Model Context Protocol · WS {socket.status} · module{" "}
            {status.data?.mcp ?? "…"}
          </p>
        </div>
        <button
          type="button"
          className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
          onClick={() => connect.mutate()}
        >
          Connect client
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          title="Connected Clients"
          value={String(st?.connectedClients ?? "…")}
          ok={(st?.connectedClients ?? 0) >= 0}
        />
        <Card title="Tools" value={String(st?.tools ?? tools.data?.tools.length ?? "…")} />
        <Card
          title="Resources"
          value={String(st?.resources ?? resources.data?.resources.length ?? "…")}
        />
        <Card
          title="Prompts"
          value={String(st?.prompts ?? prompts.data?.prompts.length ?? "…")}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Requests" value={String(st?.requests ?? 0)} />
        <Card
          title="Errors"
          value={String(st?.errors ?? 0)}
          ok={(st?.errors ?? 0) === 0}
        />
        <Card
          title="Runtime Bound"
          value={st?.runtimeBound ? "Yes" : "No"}
          ok={Boolean(st?.runtimeBound)}
        />
        <Card title="Transport" value={st?.transport ?? "…"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Registered Tools</h2>
          <ul className="max-h-64 space-y-1 overflow-y-auto text-xs">
            {(tools.data?.tools ?? []).map((t) => (
              <li key={t.name} className="flex justify-between gap-2 border-b border-[var(--border)]/40 py-1">
                <span className="font-mono text-sky-200">{t.name}</span>
                <span className="text-[var(--muted)]">{t.permission}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Resources</h2>
          <ul className="max-h-64 space-y-1 overflow-y-auto text-xs">
            {(resources.data?.resources ?? []).map((r) => (
              <li key={r.uri} className="border-b border-[var(--border)]/40 py-1">
                <div className="font-mono text-sky-200">{r.uri}</div>
                <div className="text-[var(--muted)]">{r.name}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Prompts</h2>
          <ul className="max-h-48 space-y-1 overflow-y-auto text-xs">
            {(prompts.data?.prompts ?? []).map((p) => (
              <li key={p.name} className="border-b border-[var(--border)]/40 py-1">
                <span className="font-mono text-sky-200">{p.name}</span>
                <span className="ml-2 text-[var(--muted)]">{p.description}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Sessions & Permissions</h2>
          <p className="mb-2 text-xs text-[var(--muted)]">
            Levels: {(st?.permissions ?? []).join(" · ") || "read · execute · admin"}
          </p>
          <ul className="max-h-48 space-y-1 overflow-y-auto text-xs">
            {(st?.sessions ?? []).map((s) => (
              <li key={s.id} className="border-b border-[var(--border)]/40 py-1">
                {s.clientId} · {s.permission} · req {s.requestCount}
                {s.active ? "" : " (closed)"}
              </li>
            ))}
            {(st?.sessions?.length ?? 0) === 0 && (
              <li className="text-[var(--muted)]">No sessions yet</li>
            )}
          </ul>
        </section>
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-3 text-sm font-medium">Recent Logs</h2>
        <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
          {(st?.recentLogs ?? []).map((l) => (
            <li key={l.id}>
              [{l.kind}] {l.message}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Card({
  title,
  value,
  ok,
}: {
  title: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="glass rounded-2xl border border-[var(--border)] p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
        {title}
      </div>
      <div
        className={`mt-1 truncate text-lg font-semibold ${
          ok === undefined ? "" : ok ? "text-emerald-300" : "text-rose-300"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
