import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { STRATEGY_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function StrategyStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [sources, setSources] = useState<Dict | null>(null);
  const [strategic, setStrategic] = useState<Dict | null>(null);
  const [priorities, setPriorities] = useState<Dict | null>(null);
  const [recommendations, setRecommendations] = useState<Dict | null>(null);
  const [scorecard, setScorecard] = useState<Dict | null>(null);
  const [timeline, setTimeline] = useState<Dict | null>(null);
  const [decisions, setDecisions] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: STRATEGY_STEPS[step],
      detailedExplanation:
        "The Enterprise Strategy Engine aggregates existing intelligence systems into strategic analysis and executive recommendations. It never executes business logic or changes platform state.",
      example: `Example: complete «${STRATEGY_STEPS[step]}».`,
      popup: { title: STRATEGY_STEPS[step], body: "Read-only executive strategy." },
      tooltip: STRATEGY_STEPS[step],
      purpose: "Strategic analysis and executive decision support",
      benefits: "Scorecard, priorities, roadmap and decision comparisons",
      typicalUse: "Executive Strategy Center and Decision Support Panel",
      businessValue: "Aligned priorities without operational side effects",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/strategy/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/strategy/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/strategy/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function aggregateSources() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/strategy/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "aggregate" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Aggregate failed");
      setSources(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Aggregate failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/strategy/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/strategy/sessions/${sid}/create`, {
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
      title="Enterprise Strategy Engine"
      subtitle="Read-only strategic intelligence — aggregates existing systems, never changes platform state."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Read-Only</Badge>
        <Badge>Executive</Badge>
        <Badge>Scorecard</Badge>
        <Badge>Sprint 29.18</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={STRATEGY_STEPS.length} />
      <BuilderStepNav steps={[...STRATEGY_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Strategy Engine Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load strategy engine
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
            <Card title="Data Sources">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("sources", setSources)}>
                  Load sources
                </Button>
                <Button disabled={busy} onClick={() => void aggregateSources()}>
                  Aggregate intelligence
                </Button>
              </div>
              {sources ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((sources.sources as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Strategic Overview">
              <Button disabled={busy} onClick={() => void load("overview", setStrategic)}>
                Load strategic overview
              </Button>
              {strategic ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((strategic.surfaces as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Strategic Priorities">
              <Button disabled={busy} onClick={() => void load("priorities", setPriorities)}>
                Load priorities
              </Button>
              {priorities ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((priorities.categories as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Executive Recommendations">
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

          {step === 5 ? (
            <Card title="Enterprise Scorecard">
              <Button disabled={busy} onClick={() => void load("scorecard", setScorecard)}>
                Load scorecard
              </Button>
              {scorecard ? (
                <p className="mt-3 eds-type-small">Overall: {String(scorecard.overall)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Executive Timeline">
              <Button disabled={busy} onClick={() => void load("timeline", setTimeline)}>
                Load timeline
              </Button>
              {timeline ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((timeline.segments as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Decision Support">
              <Button disabled={busy} onClick={() => void load("decisions", setDecisions)}>
                Load decision support
              </Button>
              {decisions ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((decisions.features as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
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
                  Load strategy UI
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
                Register Strategy Engine
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    strategy_engine_id:{" "}
                    {(created.strategy_engine as Dict)?.strategy_engine_id as string}
                  </li>
                  <li>
                    executive_registry_id:{" "}
                    {(created.executive_registry as Dict)?.executive_registry_id as string}
                  </li>
                  <li>
                    recommendation_registry_id:{" "}
                    {(created.recommendation_registry as Dict)?.recommendation_registry_id as string}
                  </li>
                  <li>
                    scorecard_engine_id:{" "}
                    {(created.scorecard_engine as Dict)?.scorecard_engine_id as string}
                  </li>
                  <li>
                    decision_support_api_id:{" "}
                    {(created.decision_support_api as Dict)?.decision_support_api_id as string}
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
