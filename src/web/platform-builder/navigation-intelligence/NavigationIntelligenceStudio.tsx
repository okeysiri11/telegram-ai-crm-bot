import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { NAVIGATION_INTELLIGENCE_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function NavigationIntelligenceStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [graph, setGraph] = useState<Dict | null>(null);
  const [context, setContext] = useState<Dict | null>(null);
  const [recs, setRecs] = useState<Dict | null>(null);
  const [history, setHistory] = useState<Dict | null>(null);
  const [quickAccess, setQuickAccess] = useState<Dict | null>(null);
  const [crossPlatform, setCrossPlatform] = useState<Dict | null>(null);
  const [routing, setRouting] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [query, setQuery] = useState("knowledge playbook");

  const panelHelp = useMemo(
    () => ({
      shortDescription: NAVIGATION_INTELLIGENCE_STEPS[step],
      detailedExplanation:
        "Navigation Intelligence Engine predicts, optimizes and simplifies navigation from verified context. It never executes business logic.",
      example: `Example: complete «${NAVIGATION_INTELLIGENCE_STEPS[step]}».`,
      popup: { title: NAVIGATION_INTELLIGENCE_STEPS[step], body: "Context navigation platform." },
      tooltip: NAVIGATION_INTELLIGENCE_STEPS[step],
      purpose: "Intelligent navigation recommendations",
      benefits: "Context-aware routes, recommendations, and quick access",
      typicalUse: "Navigation Hub and Recommendation Sidebar",
      businessValue: "Faster orientation without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/navigation-intelligence/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/navigation-intelligence/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/navigation-intelligence/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function runSearchRouting() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/navigation-intelligence/search-routing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Routing failed");
      setRouting(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Routing failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/navigation-intelligence/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/navigation-intelligence/sessions/${sid}/create`,
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
      title="Navigation Intelligence Engine"
      subtitle="Context navigation platform — verified context only, Workspace OS & Command Center integrated."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Logic</Badge>
        <Badge>Verified Context</Badge>
        <Badge>AI Native</Badge>
        <Badge>Sprint 29.14</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={NAVIGATION_INTELLIGENCE_STEPS.length} />
      <BuilderStepNav
        steps={[...NAVIGATION_INTELLIGENCE_STEPS]}
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
            <Card title="Navigation Intelligence Engine">
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
            <Card title="Global Navigation Graph">
              <Button disabled={busy} onClick={() => void load("graph", setGraph)}>
                Load graphs
              </Button>
              {graph ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((graph.graphs as string[]) || []).map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Context Aware Navigation">
              <Button disabled={busy} onClick={() => void load("context", setContext)}>
                Load context
              </Button>
              {context ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(context.determined, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Smart Recommendations">
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

          {step === 4 ? (
            <Card title="Navigation History">
              <Button disabled={busy} onClick={() => void load("history", setHistory)}>
                Load history
              </Button>
              {history ? (
                <p className="mt-3 eds-type-small">
                  Visited: {((history.visited_modules as unknown[]) || []).length} · Timeline{" "}
                  {((history.timeline as unknown[]) || []).length}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Quick Access">
              <Button disabled={busy} onClick={() => void load("quick-access", setQuickAccess)}>
                Load quick access
              </Button>
              {quickAccess ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((quickAccess.features as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Cross Platform Navigation">
              <Button disabled={busy} onClick={() => void load("cross-platform", setCrossPlatform)}>
                Load targets
              </Button>
              {crossPlatform ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((crossPlatform.targets as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Intelligent Search Routing">
              <div className="flex flex-wrap gap-2">
                <input
                  className="eds-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Route this search"
                />
                <Button disabled={busy} onClick={() => void runSearchRouting()}>
                  Route
                </Button>
              </div>
              {routing ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {(((routing.routed as Dict[]) || []) as Dict[]).map((r, i) => (
                    <li key={`${String(r.route)}-${i}`}>
                      {String(r.route)} · confidence {String(r.confidence)}
                    </li>
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
                  Load Navigation UI
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
                Register Navigation Intelligence
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    navigation_intelligence_engine_id:{" "}
                    {
                      (created.navigation_intelligence_engine as Dict)
                        ?.navigation_intelligence_engine_id as string
                    }
                  </li>
                  <li>
                    navigation_registry_id:{" "}
                    {(created.navigation_registry as Dict)?.navigation_registry_id as string}
                  </li>
                  <li>
                    recommendation_api_id:{" "}
                    {(created.recommendation_api as Dict)?.recommendation_api_id as string}
                  </li>
                  <li>
                    context_api_id: {(created.context_api as Dict)?.context_api_id as string}
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
