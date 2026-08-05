import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi, type ProviderDto } from "../services/runtimeApi";

function statusClass(connected: boolean, status: string): string {
  if (connected && status === "connected") return "status-ok";
  if (status === "connecting") return "status-warn";
  return "status-err";
}

export function ProvidersPage() {
  const { status, socket } = useRuntime();
  const qc = useQueryClient();
  const st = status.data;

  const providers = useQuery({
    queryKey: ["runtime", "providers"],
    queryFn: runtimeApi.providers,
    refetchInterval: 2000,
  });

  const caps = useQuery({
    queryKey: ["runtime", "providers-capabilities"],
    queryFn: runtimeApi.providerCapabilities,
    refetchInterval: 5000,
  });

  const connect = useMutation({
    mutationFn: (providerId?: string) => runtimeApi.connectProvider(providerId),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["runtime"] }),
  });
  const disconnect = useMutation({
    mutationFn: (providerId?: string) =>
      runtimeApi.disconnectProvider(providerId),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["runtime"] }),
  });
  const execute = useMutation({
    mutationFn: () =>
      runtimeApi.executeProvider({
        preferredAlias: "openai",
        capability: "chat",
        payload: { prompt: "Control Center ping" },
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["runtime"] }),
  });

  const rows = providers.data?.providers ?? [];
  const metrics = providers.data?.metrics;
  const gateway = providers.data?.gateway;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Providers</h1>
          <p className="text-sm text-[var(--muted)]">
            Provider Gateway · mock adapters · WebSocket {socket.status}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => connect.mutate(undefined)}
          >
            Connect all
          </button>
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => disconnect.mutate(undefined)}
          >
            Disconnect all
          </button>
          <button
            type="button"
            className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
            onClick={() => execute.mutate()}
          >
            Execute sample
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          title="Provider Gateway"
          value={st?.providerGateway ?? gateway?.health ?? "…"}
          ok={(st?.providerGateway ?? gateway?.health) === "OK"}
        />
        <Card
          title="Connection Status"
          value={`${gateway?.connected ?? st?.providersConnected ?? "…"} / ${gateway?.providers ?? st?.providers ?? "…"}`}
        />
        <Card title="Health" value={gateway?.health ?? "…"} ok={gateway?.health === "OK"} />
        <Card
          title="Live Metrics"
          value={`${metrics?.totalRequests ?? 0} req · ${metrics?.avgResponseTimeMs ?? 0} ms`}
        />
      </div>

      <div className="glass overflow-x-auto rounded-2xl">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-[var(--border)] text-xs uppercase tracking-widest text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Connected</th>
              <th className="px-4 py-3">Health</th>
              <th className="px-4 py-3">Capabilities</th>
              <th className="px-4 py-3">Current Requests</th>
              <th className="px-4 py-3">Avg Response</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Errors</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p: ProviderDto) => (
              <tr key={p.id} className="border-b border-[var(--border)]/50">
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3">
                  <span
                    className={`status-dot ${statusClass(p.connected, p.status)}`}
                  />{" "}
                  {p.status}
                </td>
                <td className="px-4 py-3">{p.connected ? "yes" : "no"}</td>
                <td className="px-4 py-3">{p.health?.status ?? "—"}</td>
                <td className="px-4 py-3 text-xs text-[var(--muted)]">
                  {(p.capabilities ?? []).map((c) => c.id).join(", ") || "—"}
                </td>
                <td className="px-4 py-3">{p.currentRequests}</td>
                <td className="px-4 py-3">{p.averageResponseTimeMs} ms</td>
                <td className="px-4 py-3">{p.totalRequests}</td>
                <td className="px-4 py-3">{p.errors}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="rounded border border-[var(--border)] px-2 py-1 text-xs"
                      onClick={() => connect.mutate(p.id)}
                    >
                      Connect
                    </button>
                    <button
                      type="button"
                      className="rounded border border-[var(--border)] px-2 py-1 text-xs"
                      onClick={() => disconnect.mutate(p.id)}
                    >
                      Disconnect
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <p className="p-4 text-sm text-[var(--muted)]">
            Waiting for Provider Gateway…
          </p>
        )}
      </div>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">
          Capabilities
        </h2>
        <pre className="max-h-48 overflow-auto text-xs text-[var(--muted)]">
          {JSON.stringify(caps.data?.capabilities ?? {}, null, 2)}
        </pre>
      </section>

      <section className="glass rounded-2xl p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">
          Provider Events
        </h2>
        <p className="text-sm text-[var(--muted)]">
          Live via WebSocket: provider.connected · provider.disconnected ·
          provider.health · provider.execution · provider.error
        </p>
        <div className="mt-3 max-h-40 overflow-auto font-mono text-xs">
          {socket.events
            .filter((e) => String(e.type).startsWith("provider."))
            .slice(0, 30)
            .map((e, i) => (
              <div key={`${e.type}-${i}`} className="border-b border-[var(--border)]/40 py-1">
                <span className="text-sky-200">{e.type}</span>{" "}
                {JSON.stringify(e.payload).slice(0, 120)}
              </div>
            ))}
          {!socket.events.some((e) => String(e.type).startsWith("provider.")) && (
            <p className="text-[var(--muted)]">No provider events yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function Card({
  title,
  value,
  ok = true,
}: {
  title: string;
  value: string;
  ok?: boolean;
}) {
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
