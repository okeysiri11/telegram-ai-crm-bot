/**
 * Sprint 32.0 — Workflow Builder over existing pipelines (no second WorkflowEngine).
 * Blocks: stages · approval · parallel agents · retries · templates/versions.
 */

import { Badge, Button, Card } from "@/ui";
import { useProductionStore } from "./productionStore";
import { PIPELINE_STAGES, studioById } from "./productionCatalog";

export function WorkflowBuilderPanel() {
  const pipelines = useProductionStore((s) => s.pipelines);
  const createPipeline = useProductionStore((s) => s.createPipeline);
  const advancePipeline = useProductionStore((s) => s.advancePipeline);
  const setPipelineStage = useProductionStore((s) => s.setPipelineStage);
  const setAgentChain = useProductionStore((s) => s.setAgentChain);
  const runUniversalPipeline = useProductionStore((s) => s.runUniversalPipeline);
  const activeStudioId = useProductionStore((s) => s.activeStudioId) || "creative";

  function addTemplate() {
    const studio = studioById(activeStudioId);
    createPipeline(
      `WF · ${studio?.short || activeStudioId} · ${new Date().toLocaleTimeString()}`,
      activeStudioId,
      studio?.aiAgents || ["Creative Director", "Brand Compliance"],
    );
  }

  return (
    <div className="space-y-3" data-testid="workflow-builder">
      <Card title="Workflow Builder" status={<Badge>Runtime SoR</Badge>}>
        <p className="eds-type-helper mb-2">
          Drag-equivalent stage controls · AI blocks (agents) · approval gate · parallel agents ·
          retries via Runtime. Kernel/platform WorkflowEngine remains canonical for graph workflows.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={addTemplate}>
            Новый шаблон
          </Button>
          <Button size="sm" variant="secondary" onClick={() => runUniversalPipeline(activeStudioId)}>
            Запуск (Runtime)
          </Button>
        </div>
      </Card>

      {pipelines.slice(0, 8).map((p) => (
        <Card key={p.id} title={p.title} status={<Badge tone="info">{p.stage}</Badge>}>
          <div className="mb-2 flex flex-wrap gap-1">
            {PIPELINE_STAGES.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`rounded px-2 py-1 eds-type-caption border ${
                  p.stage === s.id
                    ? "border-[var(--eds-primary)] bg-[color-mix(in_oklab,var(--eds-primary)_12%,transparent)]"
                    : "border-[var(--ew-border)]"
                }`}
                onClick={() => setPipelineStage(p.id, s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>
          <p className="eds-type-small mb-2">
            Agents (parallel): {p.agentChain.join(" · ") || "—"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={() => advancePipeline(p.id)}>
              Next stage
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setPipelineStage(p.id, "approval")}
            >
              Human Approval
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() =>
                setAgentChain(p.id, [...p.agentChain, "Reviewer", "Publisher"].slice(0, 5))
              }
            >
              + Parallel agents
            </Button>
            <Button
              size="sm"
              variant="primary"
              onClick={() => runUniversalPipeline(p.studioId, p.title)}
            >
              Execute
            </Button>
          </div>
        </Card>
      ))}
      {!pipelines.length ? <p className="eds-type-helper">Нет конвейеров — создайте шаблон.</p> : null}
    </div>
  );
}
