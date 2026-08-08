/**
 * Epic 45.3 — Universal Automation / Workflow Monitor.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

type Dash = {
  title?: string;
  active_workflows?: { id: string; status: string; step_label?: string }[];
  hercules_queue?: unknown[];
  background_jobs?: unknown[];
  cost_total?: number;
  models_used?: string[];
  errors?: unknown[];
  history?: { status?: string; run_id?: string }[];
  performance?: { runs?: number; completed?: number };
};

export function AutomationCenterPage45() {
  const [dash, setDash] = useState<Dash | null>(null);
  const [templates, setTemplates] = useState<{ title_ru: string; id: string }[]>([]);
  const [goal, setGoal] = useState("Создай рекламу салона красоты");
  const [lastRun, setLastRun] = useState<{ status?: string; step_label?: string; monitor?: Record<string, unknown> } | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, t] = await Promise.all([
        fetch("/api/v1/workflows/dashboard", { credentials: "include" }),
        fetch("/api/v1/workflows/templates", { credentials: "include" }),
      ]);
      if (d.ok) setDash((await d.json()).data || {});
      if (t.ok) setTemplates(((await t.json()).data || {}).templates || []);
    } catch {
      setDash({ title: "Owner Dashboard · Автоматизация", active_workflows: [], cost_total: 0 });
    }
  }, []);

  useEffect(() => {
    document.title = "Автоматизация · ADOS";
    void load();
  }, [load]);

  async function runGoal() {
    try {
      const res = await fetch("/api/v1/workflows/run", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, channel: "web", vertical: "beauty" }),
      });
      if (!res.ok) return;
      const json = await res.json();
      const run = json.data || {};
      setLastRun(run);
      if (run.id) {
        const st = await fetch(`/api/v1/workflows/status?run_id=${run.id}`, { credentials: "include" });
        if (st.ok) setLastRun((await st.json()).data);
      }
      void load();
    } catch {
      /* offline */
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">⚡ Автоматизация</h1>
            <p className="text-sm text-[var(--ew-muted)]">
              Цель → Planner → Workflow → Orchestrator → Hercules → Memory
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="success">Universal Automation 45.3</Badge>
            <Link to="/ai-workspace" className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm">
              Память
            </Link>
            <Link to="/ai-command" className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm">
              AI Command
            </Link>
          </div>
        </div>

        <Card title="Запустить Workflow">
          <div className="flex flex-wrap gap-2">
            <input
              className="min-w-[16rem] flex-1 rounded-md border border-[var(--ew-border)] bg-transparent px-3 py-2 text-sm"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              data-testid="wf-goal"
            />
            <button
              type="button"
              className="rounded-md border border-[var(--ew-border)] px-3 py-2 text-sm"
              onClick={() => void runGoal()}
              data-testid="wf-run"
            >
              Запустить
            </button>
          </div>
          {lastRun ? (
            <p className="mt-3 text-sm">
              Статус: {lastRun.status} · {lastRun.step_label || (lastRun.monitor as { step_label?: string } | undefined)?.step_label}
            </p>
          ) : null}
        </Card>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Card title="Активные Workflow">
            <ul className="text-sm">
              {(dash?.active_workflows || []).length === 0 ? <li className="text-[var(--ew-muted)]">Нет</li> : null}
              {(dash?.active_workflows || []).map((r) => (
                <li key={r.id}>
                  • {r.id} · {r.status} · {r.step_label}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Очередь Hercules">
            <p className="text-sm">{(dash?.hercules_queue || []).length} задач</p>
          </Card>
          <Card title="Стоимость / AI">
            <p className="text-sm">Σ {dash?.cost_total ?? 0}</p>
            <p className="text-xs text-[var(--ew-muted)]">{(dash?.models_used || []).join(", ") || "—"}</p>
          </Card>
          <Card title="Библиотека">
            <ul className="text-sm">
              {templates.slice(0, 8).map((t) => (
                <li key={t.id}>• {t.title_ru}</li>
              ))}
            </ul>
          </Card>
          <Card title="История">
            <ul className="text-sm">
              {(dash?.history || []).slice(0, 8).map((h, i) => (
                <li key={`${h.run_id}-${i}`}>
                  • {h.status} · {h.run_id}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Производительность">
            <p className="text-sm">
              Запусков: {dash?.performance?.runs ?? 0} · Завершено: {dash?.performance?.completed ?? 0}
            </p>
          </Card>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
