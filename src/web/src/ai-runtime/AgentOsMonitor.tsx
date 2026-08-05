/**
 * Sprint 32.1 — Live AgentOS monitor (Owner / Agent Center).
 */

import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { agentOs } from "@/enterprise-runtime/agentOs";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { Link } from "react-router-dom";

export function AgentOsMonitor({ compact = false }: { compact?: boolean }) {
  const [tick, setTick] = useState(0);
  const obs = useMemo(() => {
    void tick;
    return agentOs.observe();
  }, [tick]);
  const registry = useMemo(() => {
    void tick;
    return agentOs.registry();
  }, [tick]);

  function refresh() {
    setTick((t) => t + 1);
  }

  function runDemoCollab() {
    agentOs.runCollaborative({
      title: "Multi-agent production brief",
      leadAgentId: "agent_project_manager",
      workerIds: ["agent_production", "agent_brand", "agent_copywriter"],
      viaProduction: true,
      viaN8n: true,
    });
    refresh();
  }

  return (
    <div className="space-y-3" data-testid="agent-os-monitor">
      <Card title="AgentOS · Live Monitor" status={<Badge tone="success">Runtime SoR</Badge>}>
        <p className="eds-type-helper mb-2">
          SoR {obs.systemOfRecord} · n8n business logic: {String(obs.n8nBusinessLogic)} · latency ~
          {obs.latencyHintMs}ms
        </p>
        <div className="eds-grid eds-grid--dashboard">
          <div>
            <p className="eds-type-caption">Agents</p>
            <p className="font-semibold">
              {obs.health.busy}/{obs.health.total} busy
            </p>
          </div>
          <div>
            <p className="eds-type-caption">Jobs</p>
            <p className="eds-type-small">
              run {obs.jobs.running} · wait {obs.jobs.waiting} · fail {obs.jobs.failed}
            </p>
          </div>
          <div>
            <p className="eds-type-caption">Tokens / Cost</p>
            <p className="eds-type-small">
              {obs.tokens} tok · ${obs.costUsd}
            </p>
          </div>
          <div>
            <p className="eds-type-caption">Bus</p>
            <p className="eds-type-small">
              msg {obs.messages} · mem {obs.memories} · audit {obs.audit}
            </p>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" onClick={runDemoCollab}>
            Collaborative run
          </Button>
          <Button size="sm" variant="secondary" onClick={refresh}>
            Refresh
          </Button>
          <Link className="eds-type-small text-[var(--eds-primary)] self-center" to="/ai-agents">
            Agent Center →
          </Link>
          <Link className="eds-type-small text-[var(--eds-primary)] self-center" to="/production-studio">
            Production Studio →
          </Link>
        </div>
      </Card>

      {!compact ? (
        <>
          <Card title="Live Agent Map" status={<Badge>{registry.length}</Badge>}>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {registry.slice(0, 18).map((a) => (
                <div key={a.id} className="rounded-md border border-[var(--ew-border)] px-2 py-1.5">
                  <p className="font-medium eds-type-small">{a.nameRu}</p>
                  <p className="eds-type-caption">
                    {a.live?.phase || a.live?.status || "idle"} · v{a.version} ·{" "}
                    {(a.permissions || []).slice(0, 2).join(",")}
                  </p>
                </div>
              ))}
            </div>
            <p className="eds-type-helper mt-2">
              Catalog {DEFAULT_AGENTS.length} · marketplace {agentOs.marketplace().length}
            </p>
          </Card>

          <Card title="Running agents">
            <ul className="eds-type-small space-y-1">
              {obs.runningAgents.slice(0, 8).map((a) => (
                <li key={a.id}>
                  {a.name} · {a.phase} · {a.task || "—"}
                </li>
              ))}
              {!obs.runningAgents.length ? <li className="eds-type-helper">Нет running</li> : null}
            </ul>
          </Card>
        </>
      ) : null}
    </div>
  );
}
