import { useMemo, useState } from "react";
import { useRuntime } from "../context/RuntimeContext";

export function EventsPage() {
  const { events, socket } = useRuntime();
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const live = useMemo(() => {
    const rest = events.data ?? [];
    const fromWs = socket.events
      .filter((m) => m.type === "event")
      .map((m, i) => {
        const p = m.payload as { id?: string; type?: string; at?: string } | undefined;
        return {
          id: p?.id ?? `ws-${i}`,
          type: p?.type ?? "event",
          at: p?.at ?? new Date().toISOString(),
          payload: m.payload,
        };
      });
    const merged = [...fromWs, ...rest];
    const seen = new Set<string>();
    return merged.filter((e) => {
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    });
  }, [events.data, socket.events]);

  const filtered = live.filter((e) => {
    if (typeFilter && !e.type.toLowerCase().includes(typeFilter.toLowerCase())) return false;
    if (q) {
      const hay = `${e.type} ${JSON.stringify(e.payload)}`.toLowerCase();
      if (!hay.includes(q.toLowerCase())) return false;
    }
    return true;
  });

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ados-events-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Event Bus Monitor</h1>
          <p className="text-sm text-[var(--muted)]">
            Live events · WS {socket.status} · auto-refresh
          </p>
        </div>
        <button
          type="button"
          onClick={exportJson}
          className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
        >
          Export
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search…"
          className="glass rounded-xl px-3 py-2 text-sm outline-none focus:border-sky-400/40"
        />
        <input
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          placeholder="Filter type…"
          className="glass rounded-xl px-3 py-2 text-sm outline-none focus:border-sky-400/40"
        />
      </div>

      <div className="glass max-h-[70vh] overflow-auto rounded-2xl">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 border-b border-[var(--border)] bg-[var(--bg)] text-xs uppercase tracking-widest text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Id</th>
              <th className="px-4 py-3">Payload</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.id} className="border-b border-[var(--border)]/40">
                <td className="whitespace-nowrap px-4 py-2 text-xs text-[var(--muted)]">
                  {e.at}
                </td>
                <td className="px-4 py-2 font-medium text-sky-200">{e.type}</td>
                <td className="px-4 py-2 font-mono text-xs">{e.id}</td>
                <td className="px-4 py-2 font-mono text-xs text-[var(--muted)]">
                  {JSON.stringify(e.payload ?? {}).slice(0, 120)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <p className="p-4 text-sm text-[var(--muted)]">No events yet.</p>
        )}
      </div>
    </div>
  );
}
