import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { LIVE_STATUSES, OPS_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function OperationsCenterStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<Dict | null>(null);
  const [live, setLive] = useState<Dict | null>(null);
  const [activity, setActivity] = useState<Dict | null>(null);
  const [visualIds, setVisualIds] = useState<Dict | null>(null);
  const [objectId, setObjectId] = useState("ai_ops_demo");
  const [wait, setWait] = useState<Dict | null>(null);
  const [teams, setTeams] = useState<Dict | null>(null);
  const [health, setHealth] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [summary, setSummary] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: OPS_STEPS[step],
      detailedExplanation:
        "The AI Operations Center visualizes the Logical Layer in real time. It does not execute business logic.",
      example: `Example: complete «${OPS_STEPS[step]}».`,
      popup: { title: OPS_STEPS[step], body: "Enterprise visual control room." },
      tooltip: OPS_STEPS[step],
      purpose: "Real-time AI Organization visibility",
      benefits: "Operators see live status without guessing",
      typicalUse: "Control room monitoring during collaborative AI work",
      businessValue: "Foundation for Visual Layer and AI City",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/operations/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/operations/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { focus_object_id: objectId } }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/operations/${path}`);
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
      await fetch(`${PLATFORM_BUILDER_API}/operations/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/operations/sessions/${sid}/create`, {
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
      title="AI Operations Center"
      subtitle="Real-time visual control room — visualizes Logical Layer, does not execute business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Visual Control Room</Badge>
        <Badge>Live Status</Badge>
        <Badge>Sprint 29.1</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={OPS_STEPS.length} />
      <BuilderStepNav steps={[...OPS_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Operations Dashboard">
              <Button disabled={busy} onClick={() => void load("dashboard", setDashboard)}>
                Refresh dashboard
              </Button>
              {dashboard ? (
                <div className="mt-4 grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {Object.entries((dashboard.categories as Dict) || {}).map(([k, v]) => (
                    <div
                      key={k}
                      className="rounded-md border border-[var(--eds-border)] p-3 animate-[fadeIn_0.4s_ease]"
                    >
                      <div className="eds-type-caption opacity-70">{k}</div>
                      <div className="text-xl font-semibold">{String(v)}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Live Status Engine">
              <div className="mb-3 flex flex-wrap gap-2">
                {LIVE_STATUSES.map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
              </div>
              <Button disabled={busy} onClick={() => void load("live-status", setLive)}>
                Snapshot statuses
              </Button>
              {live ? (
                <div className="mt-4 grid gap-2 sm:grid-cols-3">
                  {Object.entries((live.counts as Dict) || {}).map(([k, v]) => (
                    <div
                      key={k}
                      className="rounded-md border border-[var(--eds-border)] p-2 eds-type-small"
                      style={{ animation: Number(v) > 0 ? "pulseSoft 2s ease infinite" : undefined }}
                    >
                      {k}: {String(v)}
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Realtime Activity">
              <Button disabled={busy} onClick={() => void load("activity", setActivity)}>
                Load activity feed
              </Button>
              {activity ? (
                <div className="mt-3 space-y-3">
                  {Object.entries((activity.channels as Dict) || {}).map(([channel, items]) => (
                    <div key={channel}>
                      <div className="eds-type-caption opacity-70 mb-1">{channel}</div>
                      <ul className="space-y-1 eds-type-small">
                        {((items as Dict[]) || []).slice(0, 4).map((it) => (
                          <li key={String(it.visual_id)}>
                            {String(it.label)} · {String(it.state)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Visual ID Support">
              <div className="flex flex-wrap gap-2">
                <Input value={objectId} onChange={(e) => setObjectId(e.target.value)} />
                <Button
                  disabled={busy}
                  onClick={() => void load(`visual-ids/${encodeURIComponent(objectId)}`, setVisualIds)}
                >
                  Inspect object
                </Button>
                <Button disabled={busy} onClick={() => void load("visual-ids", setVisualIds)}>
                  List all
                </Button>
              </div>
              {visualIds ? (
                <pre className="mt-3 max-h-72 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    visualIds.object ||
                      ((visualIds.objects as Dict[] | undefined) || []).slice(0, 3) ||
                      visualIds,
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Wait Experience Engine">
              <p className="eds-type-small mb-2 opacity-80">
                Never empty waiting — informative progress without misrepresenting state.
              </p>
              <Button disabled={busy} onClick={() => void load("wait-experience", setWait)}>
                Show wait experience
              </Button>
              {wait ? (
                <div className="mt-4 space-y-2">
                  <div
                    className="rounded-md border border-[var(--eds-border)] p-4"
                    style={{ animation: "waitRing 2.4s ease infinite" }}
                  >
                    <div className="eds-type-small">{String((wait.visual as Dict)?.message)}</div>
                    <div className="mt-2 h-2 overflow-hidden rounded bg-[var(--eds-border)]">
                      <div
                        className="h-full bg-[var(--eds-accent,#38bdf8)] transition-all"
                        style={{ width: `${Math.round(Number((wait.stages as Dict)?.Progress || 0) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <ul className="eds-type-small space-y-1">
                    {Object.entries((wait.stages as Dict) || {}).map(([k, v]) => (
                      <li key={k}>
                        <strong>{k}:</strong>{" "}
                        {typeof v === "object" ? JSON.stringify(v).slice(0, 80) : String(v)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Team Overview">
              <Button disabled={busy} onClick={() => void load("teams", setTeams)}>
                Load teams
              </Button>
              {teams ? (
                <div className="mt-3 grid gap-2 md:grid-cols-3 eds-type-small">
                  <div className="rounded-md border border-[var(--eds-border)] p-3">
                    Departments: {((teams.departments as unknown[]) || []).length}
                  </div>
                  <div className="rounded-md border border-[var(--eds-border)] p-3">
                    Teams: {((teams.teams as unknown[]) || []).length}
                  </div>
                  <div className="rounded-md border border-[var(--eds-border)] p-3">
                    Members: {((teams.members as unknown[]) || []).length}
                  </div>
                  <div className="rounded-md border border-[var(--eds-border)] p-3 md:col-span-3">
                    Availability {String(teams.availability)} · Workload{" "}
                    {JSON.stringify(teams.current_workload)}
                  </div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="System Health">
              <Button disabled={busy} onClick={() => void load("health", setHealth)}>
                Refresh health
              </Button>
              {health ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {Object.entries((health.surfaces as Dict) || {}).map(([k, v]) => {
                    const s = v as Dict;
                    return (
                      <div key={k} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                        <div className="font-medium">{k}</div>
                        <div>
                          {String(s.status)} — {String(s.detail)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Foundation for AI City">
              <Button disabled={busy} onClick={() => void load("ai-city", setCity)}>
                Load interfaces
              </Button>
              {city ? (
                <div className="mt-3 space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {((city.interfaces as string[]) || []).map((i) => (
                      <Badge key={i}>{i}</Badge>
                    ))}
                  </div>
                  <p className="eds-type-small opacity-70">{String(city.note)}</p>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Summary">
              <Button disabled={busy} onClick={() => void load("summary-view", setSummary)}>
                Load summary
              </Button>
              {summary ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    {
                      organization_status: summary.organization_status,
                      ai_status: summary.ai_status,
                      performance: summary.performance,
                      health: summary.health,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Create — Register Operations Surfaces">
              <p className="eds-type-small mb-3">
                Registers Operations Center, Visual Layer, and Status Engine.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    {
                      operations_center_id: (created.operations_center as Dict)?.operations_center_id,
                      visual_layer_id: (created.visual_layer as Dict)?.visual_layer_id,
                      status_engine_id: (created.status_engine as Dict)?.status_engine_id,
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
            <Button disabled={busy || step >= OPS_STEPS.length - 1} onClick={() => void go(step + 1)}>
              Next
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        @keyframes pulseSoft { 0%,100% { border-color: var(--eds-border); } 50% { border-color: var(--eds-accent, #38bdf8); } }
        @keyframes waitRing { 0%,100% { box-shadow: 0 0 0 0 rgba(56,189,248,0.35); } 50% { box-shadow: 0 0 0 8px rgba(56,189,248,0); } }
      `}</style>
    </PlatformBuilderLayout>
  );
}
