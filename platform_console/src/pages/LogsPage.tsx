import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { runtimeApi, type LogDto } from "../services/runtimeApi";

export function LogsPage() {
  const [level, setLevel] = useState<"" | "info" | "warn" | "error">("");
  const [q, setQ] = useState("");

  const logs = useQuery({
    queryKey: ["runtime", "logs", level, q],
    queryFn: async () =>
      (
        await runtimeApi.logs({
          ...(level ? { level } : {}),
          ...(q ? { q } : {}),
        })
      ).logs,
    refetchInterval: 2000,
  });

  const rows = useMemo(() => logs.data ?? [], [logs.data]);

  const download = () => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ados-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Logs</h1>
          <p className="text-sm text-[var(--muted)]">Real-time Runtime logs</p>
        </div>
        <button
          type="button"
          onClick={download}
          className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
        >
          Download
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value as typeof level)}
          className="glass rounded-xl px-3 py-2 text-sm"
        >
          <option value="">All levels</option>
          <option value="info">Info</option>
          <option value="warn">Warnings</option>
          <option value="error">Errors</option>
        </select>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search…"
          className="glass rounded-xl px-3 py-2 text-sm outline-none"
        />
      </div>

      <div className="glass max-h-[70vh] overflow-auto rounded-2xl font-mono text-xs">
        {rows.map((log: LogDto) => (
          <div
            key={log.id}
            className="border-b border-[var(--border)]/40 px-4 py-2"
          >
            <span className="text-[var(--muted)]">{log.at}</span>{" "}
            <span
              className={
                log.level === "error"
                  ? "text-[var(--err)]"
                  : log.level === "warn"
                    ? "text-[var(--warn)]"
                    : "text-[var(--ok)]"
              }
            >
              [{log.level}]
            </span>{" "}
            <span className="text-[var(--muted)]">{log.source ?? "runtime"}</span>{" "}
            {log.message}
          </div>
        ))}
        {!rows.length && (
          <p className="p-4 text-sm text-[var(--muted)]">No logs.</p>
        )}
      </div>
    </div>
  );
}
