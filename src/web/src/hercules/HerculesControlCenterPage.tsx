/**
 * Epic Hercules 1.0 — Control Center (Owner / Developer).
 * Tabs: overview, resources, GPU, CPU, queues, workers, execution, history, errors, metrics, settings.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

type TabId =
  | "overview"
  | "resources"
  | "gpu"
  | "cpu"
  | "queues"
  | "workers"
  | "execution"
  | "history"
  | "errors"
  | "metrics"
  | "settings";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Обзор" },
  { id: "resources", label: "Ресурсы" },
  { id: "gpu", label: "GPU" },
  { id: "cpu", label: "CPU" },
  { id: "queues", label: "Очереди" },
  { id: "workers", label: "Воркеры" },
  { id: "execution", label: "Выполнение" },
  { id: "history", label: "История" },
  { id: "errors", label: "Ошибки" },
  { id: "metrics", label: "Метрики" },
  { id: "settings", label: "Настройки" },
];

type Dash = {
  version?: string;
  metrics?: Record<string, number>;
  gpu?: Record<string, unknown>;
  cpu?: Record<string, unknown>;
  resources?: Record<string, unknown>;
  queues?: { hercules_lanes?: Record<string, number> };
  workers?: Array<{ id: string; kind: string; load: number; online: boolean; gpu: boolean }>;
  jobs?: Array<{ id: string; status: string; label: string; line?: string }>;
  domains?: string[];
};

async function fetchDashboard(): Promise<Dash | null> {
  try {
    const res = await fetch("/management/v1/hercules/dashboard", { credentials: "include" });
    if (!res.ok) return null;
    const json = await res.json();
    return (json.data || json) as Dash;
  } catch {
    return null;
  }
}

export function HerculesControlCenterPage() {
  const [tab, setTab] = useState<TabId>("overview");
  const [dash, setDash] = useState<Dash | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const data = await fetchDashboard();
    if (!data) {
      setError("Hercules API недоступен — показан локальный каркас.");
      setDash({
        version: "1.0.0",
        metrics: { running: 0, finished: 0, failed: 0, jobs_per_sec: 0, latency_avg_sec: 0, cost_total: 0 },
        gpu: { backend: "fallback_cpu", slots: 2, used: 0, vram_mb_est: 0, available: false },
        cpu: { cores: 4, workers: 4, active: 0, load_est: 0, ram_mb_est: 4096 },
        queues: { hercules_lanes: { ai: 0, task: 0, video: 0 } },
        workers: [],
        jobs: [],
        domains: ["crm", "erp", "ai_studio", "beauty", "telegram"],
      });
      return;
    }
    setError(null);
    setDash(data);
  }, []);

  useEffect(() => {
    void reload();
    const t = window.setInterval(() => void reload(), 8000);
    return () => window.clearInterval(t);
  }, [reload]);

  const m = dash?.metrics || {};
  const g = dash?.gpu || {};
  const c = dash?.cpu || {};

  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="hercules-control-center">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Badge tone="warning">Hercules · Owner</Badge>
            <h1 className="eds-type-title mt-2 text-2xl">Hercules Control Center</h1>
            <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
              Единое исполнительное ядро ADOS: очереди, GPU/CPU, воркеры и метрики.
            </p>
          </div>
          <div className="flex gap-3">
            <button type="button" className="eds-type-caption text-[var(--eds-accent)]" onClick={() => void reload()}>
              Обновить
            </button>
            <Link to="/platform-builder/ops-center" className="eds-type-caption text-[var(--eds-accent)]">
              ← Ops Center
            </Link>
          </div>
        </header>

        {error ? <p className="eds-type-helper text-[var(--eds-warning)]">{error}</p> : null}

        <div className="flex flex-wrap gap-2" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className={`rounded px-3 py-1.5 eds-type-caption ${
                tab === t.id
                  ? "bg-[var(--eds-accent)] text-white"
                  : "bg-[var(--eds-surface)] text-[var(--eds-text-muted)]"
              }`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <Card title={`Обзор · v${dash?.version || "—"}`}>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Выполняется" value={String(m.running ?? 0)} />
              <Stat label="Готово" value={String(m.finished ?? 0)} />
              <Stat label="Ошибки" value={String(m.failed ?? 0)} />
              <Stat label="Jobs/sec" value={String(m.jobs_per_sec ?? 0)} />
            </div>
            <p className="mt-3 eds-type-helper">
              Домены: {(dash?.domains || []).join(", ") || "—"}
            </p>
          </Card>
        )}

        {tab === "resources" && (
          <Card title="Ресурсы">
            <pre className="overflow-auto text-xs">{JSON.stringify(dash?.resources || {}, null, 2)}</pre>
          </Card>
        )}

        {tab === "gpu" && (
          <Card title="GPU">
            <p>Бэкенд: {String(g.backend)}</p>
            <p>
              Слоты: {String(g.used)}/{String(g.slots)} · VRAM ≈ {String(g.vram_mb_est)} МБ
            </p>
          </Card>
        )}

        {tab === "cpu" && (
          <Card title="CPU">
            <p>
              Ядра: {String(c.cores)} · Воркеры: {String(c.workers)} · Нагрузка ≈ {String(c.load_est)}%
            </p>
            <p>RAM ≈ {String(c.ram_mb_est)} МБ</p>
          </Card>
        )}

        {tab === "queues" && (
          <Card title="Очереди">
            <ul className="space-y-1">
              {Object.entries(dash?.queues?.hercules_lanes || {}).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {tab === "workers" && (
          <Card title="Воркеры">
            <ul className="space-y-1">
              {(dash?.workers || []).map((w) => (
                <li key={w.id}>
                  {w.id} · {w.kind} · load={w.load} {w.gpu ? "· GPU" : ""}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {(tab === "execution" || tab === "history") && (
          <Card title={tab === "execution" ? "Выполнение" : "История"}>
            <ul className="space-y-1">
              {(dash?.jobs || []).map((j) => (
                <li key={j.id}>{j.line || `${j.id} · ${j.status} · ${j.label}`}</li>
              ))}
              {!dash?.jobs?.length ? <li>Нет задач</li> : null}
            </ul>
          </Card>
        )}

        {tab === "errors" && (
          <Card title="Ошибки">
            <p>Failed: {String(m.failed ?? 0)} · Retry: {String(m.retry ?? 0)}</p>
          </Card>
        )}

        {tab === "metrics" && (
          <Card title="Метрики">
            <pre className="overflow-auto text-xs">{JSON.stringify(m, null, 2)}</pre>
          </Card>
        )}

        {tab === "settings" && (
          <Card title="Настройки">
            <p>Язык: Русский</p>
            <p>Runtime: Hercules 1.0 · единое ядро платформы</p>
            <p>API: /management/v1/hercules · /api/hercules</p>
          </Card>
        )}
      </div>
    </WorkspaceLayout>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-[var(--eds-border)] p-3">
      <div className="eds-type-helper text-[var(--eds-text-muted)]">{label}</div>
      <div className="eds-type-title text-xl">{value}</div>
    </div>
  );
}
