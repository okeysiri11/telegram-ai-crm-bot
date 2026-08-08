import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { MISSION_CONTROL_STEPS } from "./catalog";
import { MissionControlLivePanel } from "./MissionControlLivePanel";

type Dict = Record<string, unknown>;

export function MissionControlStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [operations, setOperations] = useState<Dict | null>(null);
  const [executive, setExecutive] = useState<Dict | null>(null);
  const [activity, setActivity] = useState<Dict | null>(null);
  const [panels, setPanels] = useState<Dict | null>(null);
  const [decisions, setDecisions] = useState<Dict | null>(null);
  const [resources, setResources] = useState<Dict | null>(null);
  const [timeline, setTimeline] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: MISSION_CONTROL_STEPS[step],
      detailedExplanation:
        "Mission Control is the unified executive operating center. It aggregates existing platform services and never owns business logic or replaces modules.",
      example: `Example: complete «${MISSION_CONTROL_STEPS[step]}».`,
      popup: { title: MISSION_CONTROL_STEPS[step], body: "Read-only executive operations." },
      tooltip: MISSION_CONTROL_STEPS[step],
      purpose: "Single operational interface for executive management",
      benefits: "Cockpit, timeline, risk and recommendation surfaces",
      typicalUse: "Mission Control Главная and Executive Cockpit",
      businessValue: "Unified situational awareness without module ownership",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/mission-control/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать сессию");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/mission-control/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1 }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка навигации");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/mission-control/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function aggregateOperations() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/mission-control/operations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "aggregate" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Aggregate failed");
      setOperations(body);
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
      await fetch(`${PLATFORM_BUILDER_API}/mission-control/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/mission-control/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка создания");
      setCreated(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Миссион-контроль предприятия"
      subtitle="Unified executive operating center — aggregates existing services, never replaces modules."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Read-Only</Badge>
        <Badge>Executive Cockpit</Badge>
        <Badge>Realtime</Badge>
        <Badge>Sprint 30.5</Badge>
        <Badge>Live Modules</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <MissionControlLivePanel />

      <ProgressIndicator current={step} total={MISSION_CONTROL_STEPS.length} />
      <BuilderStepNav
        steps={[...MISSION_CONTROL_STEPS]}
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
            <Card title="Mission Control Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load mission control
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
            <Card title="Unified Operations View">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("operations", setOperations)}>
                  Load operations
                </Button>
                <Button disabled={busy} onClick={() => void aggregateOperations()}>
                  Aggregate platform services
                </Button>
              </div>
              {operations ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((operations.sources as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Executive Обзор">
              <Button disabled={busy} onClick={() => void load("overview", setExecutive)}>
                Load executive overview
              </Button>
              {executive ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((executive.dimensions as string[]) || []).map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Global Activity">
              <Button disabled={busy} onClick={() => void load("activity", setActivity)}>
                Load activity streams
              </Button>
              {activity ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((activity.streams as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Mission Panels">
              <Button disabled={busy} onClick={() => void load("panels", setPanels)}>
                Load mission panels
              </Button>
              {panels ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((panels.panels as string[]) || []).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Decision Center">
              <Button disabled={busy} onClick={() => void load("decisions", setDecisions)}>
                Load decision center
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

          {step === 6 ? (
            <Card title="Resource Command View">
              <Button disabled={busy} onClick={() => void load("resources", setResources)}>
                Load resources
              </Button>
              {resources ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((resources.views as string[]) || []).map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Mission Timeline">
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

          {step === 8 ? (
            <Card title="Performance">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("performance", setPerformance)}>
                  Load performance
                </Button>
                <Button disabled={busy} onClick={() => void load("ui", setUi)}>
                  Load mission UI
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
            <Card title="Создать">
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register Mission Control
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    mission_control_id:{" "}
                    {(created.mission_control as Dict)?.mission_control_id as string}
                  </li>
                  <li>
                    executive_operations_center_id:{" "}
                    {
                      (created.executive_operations_center as Dict)
                        ?.executive_operations_center_id as string
                    }
                  </li>
                  <li>
                    mission_registry_id:{" "}
                    {(created.mission_registry as Dict)?.mission_registry_id as string}
                  </li>
                  <li>
                    executive_api_id: {(created.executive_api as Dict)?.executive_api_id as string}
                  </li>
                  <li>
                    mission_dashboard_id:{" "}
                    {(created.mission_dashboard as Dict)?.mission_dashboard_id as string}
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
