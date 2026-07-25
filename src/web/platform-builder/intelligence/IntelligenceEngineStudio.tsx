import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { INTELLIGENCE_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function IntelligenceEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [patterns, setPatterns] = useState<Dict | null>(null);
  const [anomalies, setAnomalies] = useState<Dict | null>(null);
  const [recs, setRecs] = useState<Dict | null>(null);
  const [executive, setExecutive] = useState<Dict | null>(null);
  const [heatmaps, setHeatmaps] = useState<Dict | null>(null);
  const [trends, setTrends] = useState<Dict | null>(null);
  const [health, setHealth] = useState<Dict | null>(null);
  const [predictive, setPredictive] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: INTELLIGENCE_STEPS[step],
      detailedExplanation:
        "Visual Intelligence Engine analyzes verified platform events and produces visual recommendations. It never changes business logic or generates business events.",
      example: `Example: complete «${INTELLIGENCE_STEPS[step]}».`,
      popup: { title: INTELLIGENCE_STEPS[step], body: "Enterprise visual analytics." },
      tooltip: INTELLIGENCE_STEPS[step],
      purpose: "Visual insights and health analytics",
      benefits: "Patterns, anomalies, heatmaps, and recommendations",
      typicalUse: "Executive insight center and ops dashboards",
      businessValue: "Decision support without autonomous business actions",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/intelligence/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/intelligence/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/intelligence/${path}`);
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
      await fetch(`${PLATFORM_BUILDER_API}/intelligence/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/intelligence/sessions/${sid}/create`, {
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
      title="Visual Intelligence Engine"
      subtitle="Patterns · Anomalies · Health · Recommendations — visual analytics only, no business events."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Events</Badge>
        <Badge>Verified Events Only</Badge>
        <Badge>Sprint 29.10</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={INTELLIGENCE_STEPS.length} />
      <BuilderStepNav steps={[...INTELLIGENCE_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Visual Intelligence Engine">
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
            <Card title="Pattern Detection">
              <Button disabled={busy} onClick={() => void load("patterns", setPatterns)}>
                Detect patterns
              </Button>
              {patterns ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((patterns.pattern_names as string[]) || []).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Anomaly Detection">
              <Button disabled={busy} onClick={() => void load("anomalies", setAnomalies)}>
                Identify anomalies
              </Button>
              {anomalies ? (
                <div className="mt-3 eds-type-small">
                  Active: {((anomalies.active as string[]) || []).join(", ") || "none"} · Count:{" "}
                  {String(anomalies.count)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Attention Recommendations">
              <Button disabled={busy} onClick={() => void load("recommendations", setRecs)}>
                Recommend attention
              </Button>
              {recs ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((recs.recommendation_names as string[]) || []).map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Executive Insights">
              <Button disabled={busy} onClick={() => void load("executive", setExecutive)}>
                Generate insights
              </Button>
              {executive ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((executive.insight_names as string[]) || []).map((i) => (
                    <li key={i}>{i}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Visual Heatmaps">
              <Button disabled={busy} onClick={() => void load("heatmaps", setHeatmaps)}>
                Load heatmaps
              </Button>
              {heatmaps ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((heatmaps.heatmap_names as string[]) || []).map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Trend Engine">
              <Button disabled={busy} onClick={() => void load("trends", setTrends)}>
                Explore trends
              </Button>
              {trends ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((trends.trend_names as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Visual Health Index">
              <Button disabled={busy} onClick={() => void load("health", setHealth)}>
                Calculate health
              </Button>
              {health ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Overall: {String(health.overall)}</div>
                  <div>Status: {String(health.status)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Predictive Visualization Foundation">
              <Button disabled={busy} onClick={() => void load("predictive", setPredictive)}>
                Load predictive APIs
              </Button>
              {predictive ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>
                    Autonomous decisions: {String(predictive.autonomous_business_decisions)}
                  </div>
                  <ul className="space-y-1">
                    {((predictive.api_names as string[]) || []).map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Create — Register Intelligence Stack">
              <p className="eds-type-small mb-3">
                Registers Visual Intelligence Engine, Insight Registry, Analytics Registry, and
                Recommendation Registry.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      intelligence_engine_id: (created.intelligence_engine as Dict)
                        ?.intelligence_engine_id,
                      insight_registry_id: (created.insight_registry as Dict)?.insight_registry_id,
                      analytics_registry_id: (created.analytics_registry as Dict)
                        ?.analytics_registry_id,
                      recommendation_registry_id: (created.recommendation_registry as Dict)
                        ?.recommendation_registry_id,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Back
            </Button>
            <Button
              disabled={busy || step >= INTELLIGENCE_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Next
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
