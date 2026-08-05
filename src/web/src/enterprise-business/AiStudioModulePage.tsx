/**
 * Sprint 30.8 — AI Studio hub: wires Agent Center, prompts, workflows, tasks, history, logs.
 * Composes existing runtime — no mock catalog.
 */

import { Link, useNavigate } from "react-router-dom";
import { useMemo } from "react";
import { Badge, Button, Card } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { useProductionStore } from "@/ai-production-studio/productionStore";
import { jobManager } from "@/enterprise-runtime/jobManager";

const TABS = [
  { id: "agents", label: "AI-агенты" },
  { id: "prompts", label: "Промпты" },
  { id: "workflows", label: "Процессы" },
  { id: "tasks", label: "AI-задачи" },
  { id: "history", label: "История" },
  { id: "logs", label: "Журналы" },
] as const;

export function AiStudioModulePage() {
  const navigate = useNavigate();
  const prompts = useProductionStore((s) => s.prompts);
  const pipelines = useProductionStore((s) => s.pipelines);
  const prodJobs = useProductionStore((s) => s.jobs);
  const jobs = useMemo(() => jobManager.list(), []);

  return (
    <BusinessModuleShell
      title="AI Studio"
      subtitle="Агенты · промпты · процессы · задачи · история · журналы"
      tabs={[...TABS]}
      activeTab="agents"
      onTab={(id) => {
        const map: Record<string, string> = {
          agents: "/ai-agents",
          prompts: "/ai-studio",
          workflows: "/platform-builder/workflow-center",
          tasks: "/ai-agents",
          history: "/ai-studio",
          logs: "/command-runtime",
        };
        navigate(map[id] || "/ai-studio");
      }}
      source="Runtime · Production Store"
      testId="ai-studio-module"
      actions={
        <>
          <Link to="/ai-studio">
            <Button size="sm">Открыть AI Studio</Button>
          </Link>
          <Link to="/production-studio">
            <Button size="sm" variant="secondary">
              Продакшн
            </Button>
          </Link>
        </>
      }
    >
      <div className="eds-grid eds-grid--dashboard">
        <Card title="AI Agent Center" status={<Badge tone="success">{DEFAULT_AGENTS.length}</Badge>}>
          <ul className="space-y-1 eds-type-small">
            {DEFAULT_AGENTS.slice(0, 6).map((a) => (
              <li key={a.id}>
                {a.nameRu} · {a.specialization}
              </li>
            ))}
          </ul>
          <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/ai-agents">
            Открыть центр агентов →
          </Link>
        </Card>
        <Card title="Библиотека промптов" status={<Badge>{prompts.length}</Badge>}>
          <ul className="space-y-1 eds-type-small">
            {prompts.slice(0, 6).map((p) => (
              <li key={p.id}>{p.title || p.id}</li>
            ))}
            {!prompts.length ? <li className="eds-type-helper">Откройте AI Studio для промптов</li> : null}
          </ul>
          <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/ai-studio">
            Prompt Library →
          </Link>
        </Card>
        <Card title="Workflow Builder" status={<Badge>{pipelines.length}</Badge>}>
          <p className="eds-type-helper">Конструктор процессов платформы</p>
          <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/platform-builder/workflow-center">
            Открыть →
          </Link>
        </Card>
        <Card title="AI-задачи" status={<Badge>{jobs.length + prodJobs.length}</Badge>}>
          <ul className="space-y-1 eds-type-small">
            {jobs.slice(0, 4).map((j) => (
              <li key={j.id}>
                {j.title} · {j.status}
              </li>
            ))}
            {prodJobs.slice(0, 2).map((j) => (
              <li key={j.id}>
                {j.title} · {j.status}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="История пайплайнов" status={<Badge>{pipelines.length}</Badge>}>
          <ul className="space-y-1 eds-type-small">
            {pipelines.slice(0, 6).map((h) => (
              <li key={h.id}>{h.title}</li>
            ))}
          </ul>
        </Card>
        <Card title="Журналы">
          <Link className="text-[var(--eds-primary)] eds-type-small" to="/command-runtime">
            Command Runtime →
          </Link>
          <br />
          <Link className="text-[var(--eds-primary)] eds-type-small" to="/platform-builder/runtime">
            AI Runtime →
          </Link>
        </Card>
      </div>
    </BusinessModuleShell>
  );
}
