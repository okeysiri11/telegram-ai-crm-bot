import { useRuntime } from "../context/RuntimeContext";

export function KernelPage() {
  const { kernel, services } = useRuntime();
  const k = kernel.data;

  return (
    <div className="space-y-6 fade-in">
      <h1 className="text-2xl font-semibold">Kernel</h1>
      <div className="glass grid gap-4 rounded-2xl p-5 md:grid-cols-2">
        <Field label="Kernel Version" value={k?.version} />
        <Field label="Platform Version" value={k?.platformVersion} />
        <Field label="State" value={k?.state} />
        <Field label="Health" value={k?.health} />
        <Field label="Initialization time" value={k?.startedAt} />
        <Field
          label="Uptime"
          value={k ? `${Math.floor(k.uptimeMs / 1000)}s` : undefined}
        />
        <Field label="Registered services" value={String(k?.services ?? "…")} />
      </div>
      <div className="glass rounded-2xl p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-[var(--muted)]">
          Loaded modules
        </h2>
        <ul className="space-y-2 text-sm">
          {(k?.modules ?? services.data?.map((s) => s.id) ?? []).map((id) => (
            <li key={id} className="rounded-lg border border-[var(--border)] px-3 py-2">
              {id}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-lg font-medium">{value ?? "…"}</div>
    </div>
  );
}
