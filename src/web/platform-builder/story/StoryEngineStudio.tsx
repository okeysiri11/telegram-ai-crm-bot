import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { STORY_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function StoryEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storyType, setStoryType] = useState("Executive Story");
  const [overview, setOverview] = useState<Dict | null>(null);
  const [types, setTypes] = useState<Dict | null>(null);
  const [segments, setSegments] = useState<Dict | null>(null);
  const [org, setOrg] = useState<Dict | null>(null);
  const [ai, setAi] = useState<Dict | null>(null);
  const [workflow, setWorkflow] = useState<Dict | null>(null);
  const [knowledge, setKnowledge] = useState<Dict | null>(null);
  const [executive, setExecutive] = useState<Dict | null>(null);
  const [timeline, setTimeline] = useState<Dict | null>(null);
  const [built, setBuilt] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: STORY_STEPS[step],
      detailedExplanation:
        "Движок визуальных историй groups verified Visual Event Bus events into narratives. It never creates, modifies, or reorders business events.",
      example: `Example: complete «${STORY_STEPS[step]}».`,
      popup: { title: STORY_STEPS[step], body: "Enterprise visual storytelling." },
      tooltip: STORY_STEPS[step],
      purpose: "Coherent visual narratives from real events",
      benefits: "Executive summaries and milestone timelines",
      typicalUse: "Ops storytelling and executive briefings",
      businessValue: "Trusted narratives without fabricating activity",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/story/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/story/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { story_type: storyType } }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/story/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function buildStory() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/story/build`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story_type: storyType }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Build failed");
      setBuilt(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Build failed");
    } finally {
      setBusy(false);
    }
  }

  async function navigate(action: string) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/story/navigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Navigate failed");
      setTimeline(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Navigate failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/story/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { story_type: storyType } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/story/sessions/${sid}/create`, {
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
      title="Движок визуальных историй"
      subtitle="Enterprise storytelling from verified Event Bus events — never creates or reorders business events."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Verified Events Only</Badge>
        <Badge>No Reorder</Badge>
        <Badge>Sprint 29.9</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Story type</span>
        <Input value={storyType} onChange={(e) => setStoryType(e.target.value)} />
      </div>

      <ProgressIndicator current={step} total={STORY_STEPS.length} />
      <BuilderStepNav steps={[...STORY_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Story Engine">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                  Load engine
                </Button>
                <Button disabled={busy} onClick={() => void buildStory()}>
                  Build story
                </Button>
              </div>
              {overview ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((overview.components as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
              {built ? (
                <div className="mt-3 eds-type-small">
                  Frames: {String(built.frame_count)} · Reorders:{" "}
                  {String(built.reorders_business_events)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Story Types">
              <Button disabled={busy} onClick={() => void load("types", setTypes)}>
                List types
              </Button>
              {types ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((types.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Story Segments">
              <Button disabled={busy} onClick={() => void load("segments", setSegments)}>
                Load segments
              </Button>
              {segments ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((segments.segments as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Организация Evolution">
              <Button disabled={busy} onClick={() => void load("organization", setOrg)}>
                Visualize org story
              </Button>
              {org ? (
                <div className="mt-3 eds-type-small">
                  Frames: {String((org.story as Dict)?.frame_count)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="AI Stories">
              <Button disabled={busy} onClick={() => void load("ai", setAi)}>
                Visualize AI story
              </Button>
              {ai ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((ai.beats as string[]) || []).map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Сценарий Stories">
              <Button disabled={busy} onClick={() => void load("workflow", setWorkflow)}>
                Display workflow story
              </Button>
              {workflow ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((workflow.beats as string[]) || []).map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="База знаний Stories">
              <Button disabled={busy} onClick={() => void load("knowledge", setKnowledge)}>
                Animate knowledge story
              </Button>
              {knowledge ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((knowledge.beats as string[]) || []).map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Executive Mode">
              <Button disabled={busy} onClick={() => void load("executive", setExecutive)}>
                Executive summary
              </Button>
              {executive ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>
                    Milestones:{" "}
                    {String((executive.milestone_viewer as Dict)?.count)}
                  </div>
                  <div>
                    Summaries: {((executive.summary_names as string[]) || []).join(" · ")}
                  </div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Story Навигация">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void navigate("Play")}>
                  Play
                </Button>
                <Button disabled={busy} onClick={() => void navigate("Pause")}>
                  Pause
                </Button>
                <Button disabled={busy} onClick={() => void navigate("Step")}>
                  Step
                </Button>
                <Button disabled={busy} onClick={() => void load("timeline", setTimeline)}>
                  Timeline
                </Button>
                <Button disabled={busy} onClick={() => void load("milestones", setTimeline)}>
                  Milestones
                </Button>
              </div>
              {timeline ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Cursor: {String(timeline.cursor)}</div>
                  <div>Frames: {String(timeline.frame_count)}</div>
                  <div>Paused: {String(timeline.paused)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать — зарегистрировать Story Stack">
              <p className="eds-type-small mb-3">
                Registers Story Engine, Registry, Builder, Timeline, and Executive Story API.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      story_engine_id: (created.story_engine as Dict)?.story_engine_id,
                      story_registry_id: (created.story_registry as Dict)?.story_registry_id,
                      story_builder_id: (created.story_builder as Dict)?.story_builder_id,
                      story_timeline_id: (created.story_timeline as Dict)?.story_timeline_id,
                      executive_story_api_id: (created.executive_story_api as Dict)
                        ?.executive_story_api_id,
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
              disabled={busy || step >= STORY_STEPS.length - 1}
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
