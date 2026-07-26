import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { WORKFLOW_INTELLIGENCE_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function WorkflowIntelligenceStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [graph, setGraph] = useState<Dict | null>(null);
  const [dependencies, setDependencies] = useState<Dict | null>(null);
  const [bottlenecks, setBottlenecks] = useState<Dict | null>(null);
  const [criticalPath, setCriticalPath] = useState<Dict | null>(null);
  const [resources, setResources] = useState<Dict | null>(null);
  const [recs, setRecs] = useState<Dict | null>(null);
  const [orchestration, setOrchestration] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: WORKFLOW_INTELLIGENCE_STEPS[step],
      detailedExplanation:
        "Workflow Intelligence OS analyzes, coordinates and optimizes workflow visibility. It never executes business logic directly — only visibility, dependency analysis and recommendations.",
      example: `Example: complete «${WORKFLOW_INTELLIGENCE_STEPS[step]}».`,
      popup: { title: WORKFLOW_INTELLIGENCE_STEPS[step], body: "Global process orchestrator." },
      tooltip: WORKFLOW_INTELLIGENCE_STEPS[step],
      purpose: "Workflow visibility and recommendations",
      benefits: "Dependency analysis, critical path, bottleneck detection",
      typicalUse: "Workflow Intelligence Center and Critical Path Viewer",
      businessValue: "Process clarity without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/workflow-intelligence/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/workflow-intelligence/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1 }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Navigation failed");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/workflow-intelligence/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/workflow-intelligence/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/workflow-intelligence/sessions/${sid}/create`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Create failed");
      setCreated(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Workflow Intelligence OS"
      subtitle="Global process orchestrator — visibility, dependencies and recommendations only."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Logic</Badge>
        <Badge>Critical Path</Badge>
        <Badge>Enterprise Scale</Badge>
        <Badge>Sprint 29.15</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={WORKFLOW_INTELLIGENCE_STEPS.length} />
      <BuilderStepNav
        steps={[...WORKFLOW_INTELLIGENCE_STEPS]}
        current={step}
        onChange={(i) => void go(i)}
      />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Workflow Intelligence Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load engine
              </Button>
              {overview ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((overview.components as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Global Workflow Graph">
              <Button disabled={busy} onClick={() => void load("graph", setGraph)}>
                Load graphs
              </Button>
              {graph ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((graph.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Dependency Analysis">
              <Button disabled={busy} onClick={() => void load("dependencies", setDependencies)}>
                Analyze dependencies
              </Button>
              {dependencies ? (
                <p className="mt-3 eds-type-small">Edges: {String(dependencies.count)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Bottleneck Detection">
              <Button disabled={busy} onClick={() => void load("bottlenecks", setBottlenecks)}>
                Detect bottlenecks
              </Button>
              {bottlenecks ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((bottlenecks.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Critical Path Engine">
              <Button disabled={busy} onClick={() => void load("critical-path", setCriticalPath)}>
                Calculate critical path
              </Button>
              {criticalPath ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(
                    {
                      critical_workflow: criticalPath.critical_workflow,
                      blocking_tasks: criticalPath.blocking_tasks,
                      estimated_completion: criticalPath.estimated_completion,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Resource Coordination">
              <Button disabled={busy} onClick={() => void load("resources", setResources)}>
                Load capacity
              </Button>
              {resources ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((resources.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Workflow Recommendations">
              <Button disabled={busy} onClick={() => void load("recommendations", setRecs)}>
                Load recommendations
              </Button>
              {recs ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((recs.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Enterprise Orchestration">
              <Button disabled={busy} onClick={() => void load("orchestration", setOrchestration)}>
                Load targets
              </Button>
              {orchestration ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((orchestration.targets as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Performance">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("performance", setPerformance)}>
                  Load performance
                </Button>
                <Button disabled={busy} onClick={() => void load("ui", setUi)}>
                  Load Workflow UI
                </Button>
              </div>
              {performance ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((performance.features as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
              {ui ? (
                <p className="mt-3 eds-type-small">
                  Surfaces: {((ui.surfaces as string[]) || []).join(" · ")}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Create">
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register Workflow Intelligence
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    workflow_intelligence_engine_id:{" "}
                    {
                      (created.workflow_intelligence_engine as Dict)
                        ?.workflow_intelligence_engine_id as string
                    }
                  </li>
                  <li>
                    dependency_engine_id:{" "}
                    {(created.dependency_engine as Dict)?.dependency_engine_id as string}
                  </li>
                  <li>
                    critical_path_engine_id:{" "}
                    {(created.critical_path_engine as Dict)?.critical_path_engine_id as string}
                  </li>
                  <li>
                    recommendation_engine_id:{" "}
                    {(created.recommendation_engine as Dict)?.recommendation_engine_id as string}
                  </li>
                  <li>
                    analytics_api_id: {(created.analytics_api as Dict)?.analytics_api_id as string}
                  </li>
                  <li>{String(created.message)}</li>
                </ul>
              ) : null}
            </Card>
          ) : null}
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
