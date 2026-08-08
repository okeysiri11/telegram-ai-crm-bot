import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { ANIMATIONS, BEHAVIORS, VB_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function VisualBehaviorStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [behaviors, setBehaviors] = useState<Dict | null>(null);
  const [transitions, setTransitions] = useState<Dict | null>(null);
  const [transitionResult, setTransitionResult] = useState<Dict | null>(null);
  const [animations, setAnimations] = useState<Dict | null>(null);
  const [played, setPlayed] = useState<Dict | null>(null);
  const [objectTypes, setObjectTypes] = useState<Dict | null>(null);
  const [events, setEvents] = useState<Dict | null>(null);
  const [wait, setWait] = useState<Dict | null>(null);
  const [perf, setPerf] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [logicalId, setLogicalId] = useState("ai_vb_1");
  const [toBehavior, setToBehavior] = useState("Working");
  const [animation, setAnimation] = useState("Pulse");

  const panelHelp = useMemo(
    () => ({
      shortDescription: VB_STEPS[step],
      detailedExplanation:
        "Движок визуального поведения controls how objects look and animate. It never executes business logic — only Visual Event Bus reactions.",
      example: `Example: complete «${VB_STEPS[step]}».`,
      popup: { title: VB_STEPS[step], body: "Visual-only behavior and animation." },
      tooltip: VB_STEPS[step],
      purpose: "Drive visual state from events",
      benefits: "Consistent animations without coupling to business logic",
      typicalUse: "Team Map and Operations Center visual updates",
      businessValue: "Safe foundation for AI City movement and behavior APIs",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: next + 1,
          draft: { focus_object_id: logicalId, target_behavior: toBehavior },
        }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function runTransition() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/transitions/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ logical_id: logicalId, to_behavior: toBehavior }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Transition failed");
      setTransitionResult(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Transition failed");
    } finally {
      setBusy(false);
    }
  }

  async function playAnim() {
    setBusy(true);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/animations/play`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ animation, target_id: logicalId }),
      });
      setPlayed(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function subscribe() {
    setBusy(true);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/events/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channels: ["AI Events", "Task Events"] }),
      });
      setEvents(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/visual-behavior/sessions/${sid}/create`, {
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
      title="Движок визуального поведения"
      subtitle="Visual-only behaviors & animations — reacts to Visual Event Bus, never executes business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Logic</Badge>
        <Badge>Event Bus Driven</Badge>
        <Badge>Sprint 29.3</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={VB_STEPS.length} />
      <BuilderStepNav steps={[...VB_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Движок визуального поведения">
              <Button disabled={busy} onClick={() => void load("overview", setOverview)}>
                Load engine overview
              </Button>
              {overview ? (
                <div className="mt-3 space-y-2 eds-type-small">
                  <div>State fields: {((overview.state_fields as string[]) || []).join(" · ")}</div>
                  <div>Objects: {String(overview.object_count)}</div>
                  <pre className="overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                    {JSON.stringify(overview.sample, null, 2)}
                  </pre>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Supported Behaviors">
              <Button disabled={busy} onClick={() => void load("behaviors", setBehaviors)}>
                List behaviors
              </Button>
              <div className="mt-3 flex flex-wrap gap-2">
                {(behaviors ? (behaviors.behaviors as string[]) : [...BEHAVIORS]).map((b) => (
                  <span
                    key={b}
                    className="rounded-md border border-[var(--eds-border)] px-2 py-1 eds-type-caption"
                    style={{ animation: b === "Working" ? "pulseSoft 1.6s ease infinite" : undefined }}
                  >
                    {b}
                  </span>
                ))}
              </div>
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Transition Engine">
              <Button disabled={busy} onClick={() => void load("transitions", setTransitions)}>
                Load transitions
              </Button>
              <div className="mt-3 flex flex-wrap gap-2">
                <Input value={logicalId} onChange={(e) => setLogicalId(e.target.value)} />
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={toBehavior}
                  onChange={(e) => setToBehavior(e.target.value)}
                >
                  {BEHAVIORS.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void runTransition()}>
                  Run transition
                </Button>
              </div>
              {transitions ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((transitions.supported as Dict[]) || []).map((t, i) => (
                    <li key={i}>
                      {String(t.from)} → {String(t.to)}
                    </li>
                  ))}
                </ul>
              ) : null}
              {transitionResult ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(transitionResult.transition, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Animation Framework">
              <Button disabled={busy} onClick={() => void load("animations", setAnimations)}>
                Load framework
              </Button>
              <div className="mt-3 flex flex-wrap gap-2">
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={animation}
                  onChange={(e) => setAnimation(e.target.value)}
                >
                  {ANIMATIONS.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void playAnim()}>
                  Play
                </Button>
              </div>
              {animations ? (
                <div className="mt-3 eds-type-small">
                  Pool: {JSON.stringify(animations.pool)}
                </div>
              ) : null}
              {played ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(played, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Object Types">
              <Button disabled={busy} onClick={() => void load("object-types", setObjectTypes)}>
                Load object types
              </Button>
              {objectTypes ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((objectTypes.object_types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Event Subscriptions">
              <Button disabled={busy} onClick={() => void subscribe()}>
                Subscribe to Visual Event Bus
              </Button>
              {events ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    {
                      subscription_id: events.subscription_id,
                      channels: events.channels,
                      applied: events.applied,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Wait Experience">
              <p className="eds-type-small mb-2 opacity-80">
                No empty loaders. No fake processing — only actual Visual Event Bus stages.
              </p>
              <Button disabled={busy} onClick={() => void load("wait-experience", setWait)}>
                Show wait experience
              </Button>
              {wait ? (
                <div className="mt-3 space-y-2 eds-type-small">
                  <div
                    className="rounded-md border border-[var(--eds-border)] p-3"
                    style={{ animation: "waitRing 2.2s ease infinite" }}
                  >
                    Stage: {String(wait.current_stage)} · Progress{" "}
                    {Math.round(Number(wait.current_progress || 0) * 100)}%
                  </div>
                  <div>Fake processing: {String(wait.fake_processing)}</div>
                  <ul>
                    {((wait.current_participants as Dict[]) || []).map((p) => (
                      <li key={String(p.logical_id)}>
                        {String(p.name)} — {String(p.behavior)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Performance">
              <Button disabled={busy} onClick={() => void load("performance", setPerf)}>
                Load performance profile
              </Button>
              {perf ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {Object.entries((perf.features as Dict) || {}).map(([k, v]) => (
                    <li key={k}>
                      {k}: {String(v)}
                    </li>
                  ))}
                  <li>Target FPS: {String(perf.target_fps)}</li>
                  <li>Optimized: {String(perf.optimized)}</li>
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Foundation for AI City">
              <Button disabled={busy} onClick={() => void load("ai-city-apis", setCity)}>
                Expose APIs
              </Button>
              {city ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(city.apis, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать — зарегистрировать Engines">
              <p className="eds-type-small mb-3">
                Registers Behavior Engine, Animation Framework, and Transition Engine.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(created.registrations || {
                    behavior_engine_id: (created.behavior_engine as Dict)?.behavior_engine_id,
                    animation_framework_id: (created.animation_framework as Dict)?.animation_framework_id,
                    transition_engine_id: (created.transition_engine as Dict)?.transition_engine_id,
                  }, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Назад
            </Button>
            <Button disabled={busy || step >= VB_STEPS.length - 1} onClick={() => void go(step + 1)}>
              Далее
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>

      <style>{`
        @keyframes pulseSoft { 0%,100% { border-color: var(--eds-border); } 50% { border-color: var(--eds-accent, #38bdf8); } }
        @keyframes waitRing { 0%,100% { box-shadow: 0 0 0 0 rgba(56,189,248,0.35); } 50% { box-shadow: 0 0 0 8px rgba(56,189,248,0); } }
      `}</style>
    </PlatformBuilderLayout>
  );
}
