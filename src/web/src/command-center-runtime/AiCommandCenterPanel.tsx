import { Badge, Card } from "@/ui";
import { useRuntimeHealth } from "@/shell/enterprise/useRuntimeHealth";
import { commandAnalytics } from "../../command-center/managers/analytics";
import { useMemo } from "react";
import { Link } from "react-router-dom";

type AgentRow = {
  id: string;
  name: string;
  status: "running" | "queued" | "completed";
  model: string;
  elapsed: string;
  cost: string;
};

const AGENTS: AgentRow[] = [
  { id: "a1", name: "Ops Copilot", status: "running", model: "local-demo", elapsed: "42s", cost: "$0.00" },
  { id: "a2", name: "CRM Analyst", status: "queued", model: "local-demo", elapsed: "—", cost: "—" },
  { id: "a3", name: "Knowledge Indexer", status: "completed", model: "embed-local", elapsed: "1m 12s", cost: "$0.00" },
  { id: "a4", name: "Workflow Reviewer", status: "completed", model: "local-demo", elapsed: "28s", cost: "$0.00" },
];

function statusTone(s: AgentRow["status"]): "success" | "warning" | "default" {
  if (s === "running") return "success";
  if (s === "queued") return "warning";
  return "default";
}

/** AI Command Center — running / queued / completed · providers · cost. */
export function AiCommandCenterPanel() {
  const { items } = useRuntimeHealth(30_000);
  const analytics = useMemo(() => commandAnalytics.snapshot(), []);
  const providers = items.find((i) => i.id === "providers");
  const voice = items.find((i) => i.id === "voice");
  const mcp = items.find((i) => i.id === "mcp");
  const memory = items.find((i) => i.id === "memory");
  const ai = items.find((i) => i.id === "ai");

  const running = AGENTS.filter((a) => a.status === "running");
  const queued = AGENTS.filter((a) => a.status === "queued");
  const completed = AGENTS.filter((a) => a.status === "completed");

  return (
    <section className="space-y-4" aria-label="AI Command Center">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Running agents">
          <p className="eds-type-title text-xl">{running.length}</p>
          <ul className="mt-2 space-y-1 eds-type-small">
            {running.map((a) => (
              <li key={a.id} className="flex items-center gap-2">
                <Badge tone="success">live</Badge>
                {a.name}
              </li>
            ))}
            {!running.length ? <li className="eds-type-helper">Idle</li> : null}
          </ul>
        </Card>
        <Card title="Queued">
          <p className="eds-type-title text-xl">{queued.length}</p>
          <ul className="mt-2 space-y-1 eds-type-small">
            {queued.map((a) => (
              <li key={a.id}>{a.name}</li>
            ))}
          </ul>
        </Card>
        <Card title="Completed jobs">
          <p className="eds-type-title text-xl">{completed.length}</p>
          <p className="mt-2 eds-type-helper">AI cmds tracked: {analytics.ai_usage}</p>
        </Card>
        <Card title="Estimated cost">
          <p className="eds-type-title text-xl">$0.00</p>
          <p className="mt-2 eds-type-helper">Local demo · no billable tokens</p>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Provider · Memory · Models">
          <ul className="space-y-2 eds-type-small">
            <li className="flex items-center gap-2">
              <span className={`ews-dot ews-dot--${ai?.tone || "unknown"}`} aria-hidden />
              AI · {ai?.detail || "…"}
            </li>
            <li className="flex items-center gap-2">
              <span className={`ews-dot ews-dot--${providers?.tone || "unknown"}`} aria-hidden />
              Providers · {providers?.detail || "…"}
            </li>
            <li className="flex items-center gap-2">
              <span className={`ews-dot ews-dot--${voice?.tone || "unknown"}`} aria-hidden />
              Voice · {voice?.detail || "…"}
            </li>
            <li className="flex items-center gap-2">
              <span className={`ews-dot ews-dot--${mcp?.tone || "unknown"}`} aria-hidden />
              MCP · {mcp?.detail || "…"}
            </li>
            <li className="flex items-center gap-2">
              <span className={`ews-dot ews-dot--${memory?.tone || "ok"}`} aria-hidden />
              Memory · {memory?.detail || "session"}
            </li>
          </ul>
          <Link to="/ai-agents" className="mt-3 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open AI Agents →
          </Link>
        </Card>
        <Card title="Execution · Model usage">
          <ul className="space-y-2 eds-type-small">
            {AGENTS.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2">
                <Badge tone={statusTone(a.status)}>{a.status}</Badge>
                <span className="font-medium">{a.name}</span>
                <span className="eds-type-helper">{a.model}</span>
                <span className="eds-type-helper ml-auto">{a.elapsed}</span>
                <span className="eds-type-helper">{a.cost}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 eds-type-helper">
            Avg command time · success {(analytics.success_rate * 100).toFixed(0)}%
          </p>
        </Card>
      </div>
    </section>
  );
}
