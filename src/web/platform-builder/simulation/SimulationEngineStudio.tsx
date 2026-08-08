import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { SIMULATION_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function SimulationEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simName, setSimName] = useState("AI Activation");
  const [speed, setSpeed] = useState("1");
  const [overview, setOverview] = useState<Dict | null>(null);
  const [supported, setSupported] = useState<Dict | null>(null);
  const [liveOrg, setLiveOrg] = useState<Dict | null>(null);
  const [collab, setCollab] = useState<Dict | null>(null);
  const [workflow, setWorkflow] = useState<Dict | null>(null);
  const [knowledge, setKnowledge] = useState<Dict | null>(null);
  const [document, setDocument] = useState<Dict | null>(null);
  const [timeline, setTimeline] = useState<Dict | null>(null);
  const [perf, setPerf] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [emitted, setEmitted] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: SIMULATION_STEPS[step],
      detailedExplanation:
        "Движок визуальной симуляции visualizes real platform activity from the Visual Event Bus only. Never creates fake events.",
      example: `Example: complete «${SIMULATION_STEPS[step]}».`,
      popup: { title: SIMULATION_STEPS[step], body: "Live enterprise simulation." },
      tooltip: SIMULATION_STEPS[step],
      purpose: "Visualize real enterprise activity",
      benefits: "Bus-originated timeline and live feeds",
      typicalUse: "Ops rooms and organization activity views",
      businessValue: "Trustworthy live visualization without fabricated events",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/simulation/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/simulation/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { speed: Number(speed) || 1 } }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/simulation/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function emit() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/simulation/emit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ simulation: simName }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Emit failed");
      setEmitted(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Emit failed");
    } finally {
      setBusy(false);
    }
  }

  async function timelineAction(action: string) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/simulation/timeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          speed: action.toLowerCase().includes("speed") ? Number(speed) || 1 : undefined,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Timeline action failed");
      setTimeline(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Timeline action failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/simulation/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { speed: Number(speed) || 1 } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/simulation/sessions/${sid}/create`, {
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
      title="Движок визуальной симуляции"
      subtitle="Live enterprise simulation from Visual Event Bus — never creates fake events."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Event Bus Only</Badge>
        <Badge>No Fake Events</Badge>
        <Badge>Sprint 29.7</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Симуляция</span>
        <Input value={simName} onChange={(e) => setSimName(e.target.value)} />
        <span className="eds-type-small">Speed</span>
        <Input value={speed} onChange={(e) => setSpeed(e.target.value)} />
      </div>

      <ProgressIndicator current={step} total={SIMULATION_STEPS.length} />
      <BuilderStepNav steps={[...SIMULATION_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Движок симуляции">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                  Load engine
                </Button>
                <Button disabled={busy} onClick={() => void load("ui", setUi)}>
                  UI dashboard
                </Button>
              </div>
              {overview ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((overview.components as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
              {ui ? (
                <div className="mt-3 eds-type-small">
                  Active: {String(ui.active_simulation_counter)} · Queue:{" "}
                  {(((ui.current_simulation_queue as unknown[]) || []) as unknown[]).length}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Supported Симуляцияs">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("supported", setSupported)}>
                  List simulations
                </Button>
                <Button disabled={busy} onClick={() => void emit()}>
                  Emit via Event Bus
                </Button>
              </div>
              {supported ? (
                <div className="mt-3 eds-type-small">Count: {String(supported.count)}</div>
              ) : null}
              {emitted ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Event: {String((emitted.event as Dict)?.event_id)}</div>
                  <div>Fake: {String(emitted.creates_fake_events)}</div>
                  <div>Origin: {String((emitted.frame as Dict)?.origin)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Live Организация Симуляция">
              <Button disabled={busy} onClick={() => void load("live-organization", setLiveOrg)}>
                Load live org
              </Button>
              {liveOrg ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((liveOrg.surfaces as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="AI Collaboration">
              <Button disabled={busy} onClick={() => void load("collaboration", setCollab)}>
                Visualize collaboration
              </Button>
              {collab ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((collab.visuals as string[]) || []).map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Сценарий Симуляция">
              <Button disabled={busy} onClick={() => void load("workflow", setWorkflow)}>
                Animate workflow
              </Button>
              {workflow ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((workflow.stages as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="База знаний Flow">
              <Button disabled={busy} onClick={() => void load("knowledge", setKnowledge)}>
                Visualize knowledge
              </Button>
              {knowledge ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((knowledge.stages as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Document Flow">
              <Button disabled={busy} onClick={() => void load("document", setDocument)}>
                Animate documents
              </Button>
              {document ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((document.stages as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Симуляция Timeline">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void timelineAction("Pause")}>
                  Pause
                </Button>
                <Button disabled={busy} onClick={() => void timelineAction("Resume")}>
                  Resume
                </Button>
                <Button disabled={busy} onClick={() => void timelineAction("Speed Control")}>
                  Speed
                </Button>
                <Button disabled={busy} onClick={() => void timelineAction("Step Forward")}>
                  Step
                </Button>
              </div>
              {timeline ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Paused: {String(timeline.paused)}</div>
                  <div>Speed: {String(timeline.speed)}</div>
                  <div>Frames: {String(timeline.frame_count)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Performance">
              <Button disabled={busy} onClick={() => void load("performance", setPerf)}>
                Optimize
              </Button>
              {perf ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((perf.feature_names as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать — зарегистрировать Симуляция Stack">
              <p className="eds-type-small mb-3">
                Registers Движок симуляции, Симуляция Registry, Timeline Engine, and Симуляция API.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      simulation_engine_id: (created.simulation_engine as Dict)
                        ?.simulation_engine_id,
                      simulation_registry_id: (created.simulation_registry as Dict)
                        ?.simulation_registry_id,
                      timeline_engine_id: (created.timeline_engine as Dict)?.timeline_engine_id,
                      simulation_api_id: (created.simulation_api as Dict)?.simulation_api_id,
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
              Назад
            </Button>
            <Button
              disabled={busy || step >= SIMULATION_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Далее
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
