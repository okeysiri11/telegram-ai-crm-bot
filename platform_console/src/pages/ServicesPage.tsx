import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

export function ServicesPage() {
  const { services } = useRuntime();
  const qc = useQueryClient();
  const stop = useMutation({
    mutationFn: runtimeApi.stopService,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runtime", "services"] }),
  });
  const restart = useMutation({
    mutationFn: runtimeApi.restartService,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runtime", "services"] }),
  });

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Services</h1>
      <div className="glass overflow-x-auto rounded-2xl">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-[var(--border)] text-xs uppercase tracking-widest text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3">Service</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Version</th>
              <th className="px-4 py-3">Dependencies</th>
              <th className="px-4 py-3">Startup / Uptime</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(services.data ?? []).map((s) => (
              <tr key={s.id} className="border-b border-[var(--border)]/60">
                <td className="px-4 py-3 font-medium">{s.id}</td>
                <td className="px-4 py-3">
                  <span className="mr-2 inline-block">
                    <span
                      className={`status-dot ${
                        s.health === "healthy" ? "status-ok" : "status-warn"
                      }`}
                    />
                  </span>
                  {s.lifecycle} / {s.health}
                </td>
                <td className="px-4 py-3">{s.version}</td>
                <td className="px-4 py-3 text-[var(--muted)]">
                  {s.dependencies.length ? s.dependencies.join(", ") : "—"}
                </td>
                <td className="px-4 py-3">{Math.floor(s.uptimeMs / 1000)}s</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-[var(--border)] px-2 py-1 text-xs hover:bg-white/5"
                      onClick={() => restart.mutate(s.id)}
                    >
                      Restart
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-[var(--border)] px-2 py-1 text-xs hover:bg-white/5"
                      onClick={() => stop.mutate(s.id)}
                    >
                      Stop
                    </button>
                    <details className="text-xs text-[var(--muted)]">
                      <summary className="cursor-pointer">View Details</summary>
                      <pre className="mt-2 max-w-xs overflow-auto rounded bg-black/30 p-2">
                        {JSON.stringify(s, null, 2)}
                      </pre>
                    </details>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
