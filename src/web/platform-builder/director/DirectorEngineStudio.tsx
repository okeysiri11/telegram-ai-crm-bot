import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { DIRECTOR_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function DirectorEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sceneName, setSceneName] = useState("Live Ops");
  const [overview, setOverview] = useState<Dict | null>(null);
  const [scenes, setScenes] = useState<Dict | null>(null);
  const [focus, setFocus] = useState<Dict | null>(null);
  const [attention, setAttention] = useState<Dict | null>(null);
  const [coord, setCoord] = useState<Dict | null>(null);
  const [liveOrg, setLiveOrg] = useState<Dict | null>(null);
  const [camera, setCamera] = useState<Dict | null>(null);
  const [conflicts, setConflicts] = useState<Dict | null>(null);
  const [perf, setPerf] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: DIRECTOR_STEPS[step],
      detailedExplanation:
        "Visual Director Engine orchestrates how visual events are presented. It does not generate business events.",
      example: `Example: complete «${DIRECTOR_STEPS[step]}».`,
      popup: { title: DIRECTOR_STEPS[step], body: "Intelligent scene orchestration." },
      tooltip: DIRECTOR_STEPS[step],
      purpose: "Coordinate visual presentation",
      benefits: "Focus, attention, and conflict-free scenes",
      typicalUse: "Ops rooms and executive overviews",
      businessValue: "Clear visual direction without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/director/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/director/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { scene_name: sceneName } }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/director/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function createScene() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/director/scenes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: sceneName }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Scene create failed");
      await fetch(`${PLATFORM_BUILDER_API}/director/scenes/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene_id: body.scene_id }),
      });
      await load("scenes", setScenes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scene create failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/director/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { scene_name: sceneName } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/director/sessions/${sid}/create`, {
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
      title="Visual Director Engine"
      subtitle="Scene orchestration · Focus · Attention — presentation only, no business events."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Presentation Only</Badge>
        <Badge>No Business Events</Badge>
        <Badge>Sprint 29.8</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Scene name</span>
        <Input value={sceneName} onChange={(e) => setSceneName(e.target.value)} />
      </div>

      <ProgressIndicator current={step} total={DIRECTOR_STEPS.length} />
      <BuilderStepNav steps={[...DIRECTOR_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Director Engine">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                  Load director
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
                  Focus: {String((ui.live_focus_indicator as Dict)?.target)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Scene Management">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("scenes", setScenes)}>
                  List scenes
                </Button>
                <Button disabled={busy} onClick={() => void createScene()}>
                  Create & switch
                </Button>
              </div>
              {scenes ? (
                <div className="mt-3 eds-type-small">
                  Count: {String(scenes.count)} · Active:{" "}
                  {String((scenes.scene_status as Dict)?.active_scene_id)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Focus Engine">
              <Button disabled={busy} onClick={() => void load("focus", setFocus)}>
                Resolve focus
              </Button>
              {focus ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Primary: {String((focus.primary_focus as Dict)?.target)}</div>
                  <div>Ref: {String((focus.primary_focus as Dict)?.ref)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Attention Management">
              <Button disabled={busy} onClick={() => void load("attention", setAttention)}>
                Coordinate attention
              </Button>
              {attention ? (
                <div className="mt-3 eds-type-small">
                  Highlight: {String((attention.current_highlight as Dict)?.label)} · Queue:{" "}
                  {(((attention.attention_queue as unknown[]) || []) as unknown[]).length}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Simulation Coordination">
              <Button disabled={busy} onClick={() => void load("coordination", setCoord)}>
                Coordinate engines
              </Button>
              {coord ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((coord.engines as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Live Organization">
              <Button disabled={busy} onClick={() => void load("live-organization", setLiveOrg)}>
                Direct live org
              </Button>
              {liveOrg ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((liveOrg.directives as string[]) || []).map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Intelligent Camera API">
              <Button disabled={busy} onClick={() => void load("camera", setCamera)}>
                Load camera
              </Button>
              {camera ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(camera.camera, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Conflict Resolution">
              <Button disabled={busy} onClick={() => void load("conflicts", setConflicts)}>
                Resolve conflicts
              </Button>
              {conflicts ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((conflicts.preventions as string[]) || []).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
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
            <Card title="Create — Register Director Stack">
              <p className="eds-type-small mb-3">
                Registers Director Engine, Scene Manager, Focus Manager, and Priority Manager.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      director_engine_id: (created.director_engine as Dict)?.director_engine_id,
                      scene_manager_id: (created.scene_manager as Dict)?.scene_manager_id,
                      focus_manager_id: (created.focus_manager as Dict)?.focus_manager_id,
                      priority_manager_id: (created.priority_manager as Dict)?.priority_manager_id,
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
              disabled={busy || step >= DIRECTOR_STEPS.length - 1}
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
