/**
 * Studio workbench — Sprint 28.3.
 * Per-studio generation UI over existing Production Runtime.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { useAiAgentRuntime } from "@/enterprise-runtime/useRuntimeEngine";
import { studioById, type ProductionStudioId } from "./productionCatalog";
import { useProductionStore } from "./productionStore";

export function StudioWorkbench({ studioId }: { studioId: ProductionStudioId }) {
  const studio = studioById(studioId)!;
  const generate = useProductionStore((s) => s.generateInStudio);
  const suggestPrompts = useProductionStore((s) => s.suggestPrompts);
  const recommendAgents = useProductionStore((s) => s.recommendAgents);
  const setView = useProductionStore((s) => s.setView);
  const createProject = useProductionStore((s) => s.createProject);
  const activeProjectId = useProductionStore((s) => s.activeProjectId);
  const agentsLive = useAiAgentRuntime();
  const suggestions = useMemo(() => suggestPrompts(studioId), [studioId, suggestPrompts]);
  const recommended = useMemo(() => recommendAgents(studioId), [studioId, recommendAgents]);
  const [promptId, setPromptId] = useState(suggestions[0]?.id || "");
  const [multiAgent, setMultiAgent] = useState(true);
  const [vars, setVars] = useState<Record<string, string>>({});
  const prompt = suggestions.find((p) => p.id === promptId) || suggestions[0];

  return (
    <Card title={studio.label} status={<Badge tone="info">{studio.group}</Badge>}>
      <p className="eds-type-helper mb-3">{studio.description}</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="stack-sm">
          <p className="eds-type-caption">Prompt template</p>
          <select
            className="eds-input"
            value={prompt?.id || ""}
            onChange={(e) => setPromptId(e.target.value)}
            aria-label="Prompt template"
          >
            {suggestions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
          {prompt?.variables.map((v) => (
            <Input
              key={v}
              placeholder={`{{${v}}}`}
              value={vars[v] || ""}
              onChange={(e) => setVars((prev) => ({ ...prev, [v]: e.target.value }))}
              aria-label={v}
            />
          ))}
          <label className="eds-type-helper row" style={{ gap: 8 }}>
            <input
              type="checkbox"
              checked={multiAgent}
              onChange={(e) => setMultiAgent(e.target.checked)}
            />
            Multi-agent execution
          </label>
        </div>
        <div className="stack-sm">
          <p className="eds-type-caption">Agent recommendations</p>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {recommended.map((a) => (
              <Badge key={a} tone="info">
                {a}
              </Badge>
            ))}
          </div>
          <p className="eds-type-caption mt-2">Live runtime agents</p>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {agentsLive
              .filter((a) => recommended.some((r) => r.toLowerCase() === a.name.toLowerCase()) || a.status === "busy")
              .slice(0, 6)
              .map((a) => (
                <Badge key={a.id} tone={a.status === "busy" ? "warning" : "success"}>
                  {a.name} · {a.status}
                </Badge>
              ))}
          </div>
          <p className="eds-type-helper mt-2">Automatic suggestions from favorites + studio category.</p>
        </div>
      </div>
      <div className="row mt-4" style={{ gap: 8, flexWrap: "wrap" }}>
        <Button
          size="sm"
          onClick={() =>
            generate(studioId, {
              promptId: prompt?.id,
              variables: vars,
              multiAgent,
              projectId: activeProjectId || undefined,
            })
          }
        >
          Generate via Runtime
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => createProject(`${studio.short} project`, studioId, studio.description)}
        >
          New project
        </Button>
        {studio.deepLink ? (
          <Link to={studio.deepLink}>
            <Button size="sm" variant="ghost">
              Linked module
            </Button>
          </Link>
        ) : null}
        <Button size="sm" variant="ghost" onClick={() => setView("home")}>
          All studios
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setView("prompts")}>
          Prompt Studio
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setView("projects")}>
          Projects
        </Button>
      </div>
    </Card>
  );
}
