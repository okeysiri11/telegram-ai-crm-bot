import { RUNTIME_HTTP, RUNTIME_WS } from "../services/runtimeApi";
import { useRuntime } from "../context/RuntimeContext";

export function OsSettingsPage() {
  const { connected, status } = useRuntime();

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <div className="glass space-y-4 rounded-2xl p-6 text-sm">
        <Row label="Runtime HTTP" value={RUNTIME_HTTP} />
        <Row label="Runtime WebSocket" value={RUNTIME_WS} />
        <Row label="Connection" value={connected ? "Connected" : "Disconnected"} />
        <Row label="Platform version" value={status.data?.version ?? "…"} />
        <Row label="System status" value={status.data?.systemStatus ?? "…"} />
        <p className="pt-2 text-[var(--muted)]">
          Override with <code className="text-sky-200">VITE_RUNTIME_URL</code> and{" "}
          <code className="text-sky-200">VITE_RUNTIME_WS</code>.
        </p>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-wrap justify-between gap-2 border-b border-[var(--border)] pb-3">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="font-mono text-xs">{value}</span>
    </div>
  );
}
