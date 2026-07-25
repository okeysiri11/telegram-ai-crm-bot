import { buildExecutiveDashboard, agentRegistry } from "../dashboard/executiveDashboard";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

export function AIOSPage() {
  const dash = buildExecutiveDashboard();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">Sprint 27.1 · Multi-Agent OS · v{dash.version}</p>
          <h1 className="eds-type-h1">{dash.title}</h1>
          <p className="eds-type-body text-[var(--eds-text-muted)]">
            Executive AI Director · Agent Registry 2.0 · Communication Bus · Task Orchestrator · Collaboration
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>Active {dash.activeCount}</Badge>
            <Badge>Agents {dash.agentsTotal}</Badge>
            <Badge>Latency {dash.latencyMsAvg} ms</Badge>
            <Badge>Cost ${dash.cost}</Badge>
          </div>
        </header>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Active agents">
            <ul className="space-y-1 eds-type-small">
              {dash.agents.filter((a) => a.status === "busy").map((a) => (
                <li key={a.agentId}>{a.name}</li>
              ))}
              {dash.activeCount === 0 ? <li className="text-[var(--eds-text-muted)]">None busy</li> : null}
            </ul>
          </Card>
          <Card title="Queues">
            <p className="eds-type-small">Bus: {dash.queueBus}</p>
            <p className="eds-type-small">Priority: {dash.queuePriority}</p>
          </Card>
          <Card title="Load">
            <ul className="max-h-40 space-y-1 overflow-auto eds-type-small">
              {dash.agents.map((a) => (
                <li key={a.agentId}>
                  {a.name}: {(a.load * 100).toFixed(0)}%
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Cost & latency">
            <p className="eds-type-small">Cost: ${dash.cost}</p>
            <p className="eds-type-small">Avg latency: {dash.latencyMsAvg} ms</p>
          </Card>
          <Card title="Errors">
            {dash.errors.length === 0 ? (
              <p className="eds-type-small text-[var(--eds-text-muted)]">None</p>
            ) : (
              <ul className="space-y-1 eds-type-small">
                {dash.errors.map((e, i) => (
                  <li key={i}>{e.error}</li>
                ))}
              </ul>
            )}
          </Card>
          <Card title="Task history">
            <ul className="space-y-1 eds-type-small">
              {dash.taskHistory.map((t, i) => (
                <li key={i}>{t.goal || t.name || t.taskId} · {t.status || (t.ok ? "ok" : "")}</li>
              ))}
            </ul>
          </Card>
        </div>

        <Card title="Agent Registry 2.0">
          <ul className="space-y-2 eds-type-small">
            {agentRegistry.list().map((a) => (
              <li key={a.agentId} className="rounded-md border border-[var(--eds-border)] p-2">
                <div className="flex flex-wrap items-center gap-2">
                  <strong>{a.name}</strong>
                  <Badge>{a.role}</Badge>
                  <Badge>{a.status}</Badge>
                </div>
                <p className="eds-type-caption mt-1">
                  caps: {a.capabilities.join(", ")} · models: {a.models.join(", ")} · cost {a.cost}/1k · {a.speed} tps · {a.memory} MB
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
