import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { TWIN_INTELLIGENCE_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function TwinIntelligenceStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [scenarios, setScenarios] = useState<Dict | null>(null);
  const [whatIf, setWhatIf] = useState<Dict | null>(null);
  const [impact, setImpact] = useState<Dict | null>(null);
  const [risk, setRisk] = useState<Dict | null>(null);
  const [capacity, setCapacity] = useState<Dict | null>(null);
  const [recommendations, setRecommendations] = useState<Dict | null>(null);
  const [comparison, setComparison] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: TWIN_INTELLIGENCE_STEPS[step],
      detailedExplanation:
        "Digital Twin Intelligence analyzes verified twin data only. It never changes platform state, executes workflows, or modifies business logic.",
      example: `Example: complete «${TWIN_INTELLIGENCE_STEPS[step]}».`,
      popup: { title: TWIN_INTELLIGENCE_STEPS[step], body: "Read-only scenario intelligence." },
      tooltip: TWIN_INTELLIGENCE_STEPS[step],
      purpose: "Analytical insights from verified Digital Twin state",
      benefits: "Scenario, impact, risk, capacity and recommendation analysis",
      typicalUse: "Scenario Center and Recommendation Center",
      businessValue: "Decision support without operational side effects",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function prepareScenario() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "prepare", type: "Current State" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Scenario prepare failed");
      setScenarios(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scenario prepare failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/twin-intelligence/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
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
      title="Digital Twin Intelligence"
      subtitle="Read-only analysis of verified Digital Twin data — never changes platform state."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Read-Only</Badge>
        <Badge>Scenario Analysis</Badge>
        <Badge>Verified Twin Data</Badge>
        <Badge>Sprint 29.17</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={TWIN_INTELLIGENCE_STEPS.length} />
      <BuilderStepNav steps={[...TWIN_INTELLIGENCE_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Digital Twin Intelligence">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load intelligence engine
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
            <Card title="Scenario Analysis">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("scenarios", setScenarios)}>
                  Load scenarios
                </Button>
                <Button disabled={busy} onClick={() => void prepareScenario()}>
                  Prepare current-state scenario
                </Button>
              </div>
              {scenarios ? (
                <p className="mt-3 eds-type-small">
                  Scenarios: {((scenarios.scenarios as unknown[]) || []).length}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="What-If Engine">
              <Button disabled={busy} onClick={() => void load("what-if", setWhatIf)}>
                Load what-if actions
              </Button>
              {whatIf ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((whatIf.actions as string[]) || []).map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Impact Analysis">
              <Button disabled={busy} onClick={() => void load("impact", setImpact)}>
                Load impact dashboard
              </Button>
              {impact ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((impact.dimensions as string[]) || []).map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Risk Analysis">
              <Button disabled={busy} onClick={() => void load("risk", setRisk)}>
                Load risk dashboard
              </Button>
              {risk ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((risk.categories as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Capacity Analysis">
              <Button disabled={busy} onClick={() => void load("capacity", setCapacity)}>
                Load capacity dashboard
              </Button>
              {capacity ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((capacity.dimensions as string[]) || []).map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Recommendation Engine">
              <Button disabled={busy} onClick={() => void load("recommendations", setRecommendations)}>
                Load recommendations
              </Button>
              {recommendations ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((recommendations.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Scenario Comparison">
              <Button disabled={busy} onClick={() => void load("comparison", setComparison)}>
                Load comparison
              </Button>
              {comparison ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((comparison.modes as string[]) || []).map((m) => (
                    <li key={m}>{m}</li>
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
                  Load intelligence UI
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
                Register Twin Intelligence
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    twin_intelligence_engine_id:{" "}
                    {
                      (created.twin_intelligence_engine as Dict)
                        ?.twin_intelligence_engine_id as string
                    }
                  </li>
                  <li>
                    scenario_engine_id:{" "}
                    {(created.scenario_engine as Dict)?.scenario_engine_id as string}
                  </li>
                  <li>
                    impact_engine_id: {(created.impact_engine as Dict)?.impact_engine_id as string}
                  </li>
                  <li>risk_engine_id: {(created.risk_engine as Dict)?.risk_engine_id as string}</li>
                  <li>
                    twin_recommendation_engine_id:{" "}
                    {
                      (created.twin_recommendation_engine as Dict)
                        ?.twin_recommendation_engine_id as string
                    }
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
