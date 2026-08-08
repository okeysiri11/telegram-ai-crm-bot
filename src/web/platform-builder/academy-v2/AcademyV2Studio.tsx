import { useMemo, useState } from "react";
import { Badge, Button, Card, Input, Switch } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { useAcademyStore } from "../managers/academyStore";
import { ACADEMY_MODES } from "../managers/builderRegistry";
import { PLATFORM_BUILDER_API } from "../types";
import {
  ACADEMY_V2_STEPS,
  EXPERIENCE_LEVELS,
  HELP_FIELDS,
  RECOMMENDATION_TYPES,
} from "./catalog";

export function AcademyV2Studio() {
  const [step, setStep] = useState(0);
  const [level, setLevel] = useState("beginner");
  const [question, setQuestion] = useState("What modules should I pick first?");
  const [guide, setGuide] = useState<Record<string, unknown> | null>(null);
  const [help, setHelp] = useState<Record<string, unknown> | null>(null);
  const [recs, setRecs] = useState<Record<string, unknown> | null>(null);
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [impact, setImpact] = useState<Record<string, unknown> | null>(null);
  const [learning, setLearning] = useState<Record<string, unknown> | null>(null);
  const [progress, setProgress] = useState<Record<string, unknown> | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mode = useAcademyStore((s) => s.mode);
  const setMode = useAcademyStore((s) => s.setMode);
  const experienceLevel = useAcademyStore((s) => s.experienceLevel);
  const setExperienceLevel = useAcademyStore((s) => s.setExperienceLevel);
  const learningEnabled = useAcademyStore((s) => s.isLearningEnabled("academy"));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const guided = learningEnabled && mode === "guided_learning";

  const panelHelp = useMemo(
    () => ({
      shortDescription: ACADEMY_V2_STEPS[step],
      detailedExplanation:
        "Academy 2.0 adapts every Builder to your experience level with contextual help, AI Guide, recommendations, and progress.",
      example: `Example: complete «${ACADEMY_V2_STEPS[step]}».`,
      popup: { title: ACADEMY_V2_STEPS[step], body: "Вы не потеряетесь внутри конструктора." },
      tooltip: ACADEMY_V2_STEPS[step],
      purpose: "Интерактивное обучение для каждого конструктора",
      benefits: "Faster onboarding and better configurations",
      typicalUse: "При создании вертикалей, AI или консьержа",
      businessValue: "Higher builder quality with less rework",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "owner" }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать Academy session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function loadLevel(id: string) {
    setLevel(id);
    setExperienceLevel(id as typeof experienceLevel);
    const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/levels/${id}`);
    if (res.ok) {
      /* adaptations applied via store */
    }
  }

  async function loadHelp(field: string) {
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/academy/v2/help/${field}?builder_id=vertical`,
      );
      setHelp(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runGuide() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          builder_id: "vertical",
          step: ACADEMY_V2_STEPS[step],
          question,
          level,
          draft: {
            name: "Demo Clinic",
            modules: ["crm", "knowledge_base"],
            knowledge_topics: [],
          },
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Guide failed");
      setGuide(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Guide failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadRecs() {
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/academy/v2/recommendations?builder_id=vertical&industry=medical`,
      );
      setRecs(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadLearning() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/learning?user_id=owner`);
      setLearning(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runAnalysis() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          builder_id: "vertical",
          draft: {
            name: "Demo Clinic",
            modules: ["crm"],
            knowledge_topics: [],
          },
        }),
      });
      setAnalysis(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadImpact() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/impact/crm?name=CRM`);
      setImpact(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadProgress() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/progress?user_id=owner`);
      setProgress(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function syncAndCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      const patch = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: 10,
          draft: {
            experience_level: level,
            builder_id: "vertical",
            industry: "medical",
            enable_ai_guide: true,
            enable_recommendations: true,
            completed_lessons: ["intro", "help", "guide", "recommend"],
            draft_snapshot: {
              name: "Demo Clinic",
              modules: ["crm", "knowledge_base", "analytics"],
              ai_mode: "connect_existing",
              knowledge_topics: ["SOPs"],
              dashboard_widgets: ["kpi_overview"],
            },
          },
        }),
      });
      const patchBody = await patch.json();
      if (!patch.ok) throw new Error(patchBody.error || "Ошибка сохранения");
      const create = await fetch(`${PLATFORM_BUILDER_API}/academy/v2/sessions/${sid}/create`, {
        method: "POST",
        body: "{}",
      });
      const createBody = await create.json();
      if (!create.ok) throw new Error(createBody.error || "Ошибка создания");
      setCreated(createBody);
      setProgress(createBody.progress as Record<string, unknown>);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Академия конструктора 2.0"
      subtitle="Интерактивное обучение для каждого конструктора — adaptive levels, AI Guide, recommendations, and progress."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Operational</Badge>
        <Badge>AI Guide</Badge>
        <Badge>Level · {level}</Badge>
        <Badge>Mode · {mode}</Badge>
        <Switch
          checked={learningEnabled}
          onChange={(v) => toggleLearning("academy", v)}
          label="Режим обучения"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {ACADEMY_MODES.map((m) => (
          <Button
            key={m.id}
            variant={mode === m.id ? "primary" : "ghost"}
            onClick={() => setMode(m.id)}
          >
            {m.name}
          </Button>
        ))}
      </div>

      <ProgressIndicator current={step} total={ACADEMY_V2_STEPS.length} />
      <BuilderStepNav steps={[...ACADEMY_V2_STEPS]} current={step} onChange={setStep} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={ACADEMY_V2_STEPS[step]}>
          {step === 0 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {EXPERIENCE_LEVELS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`rounded-md border p-3 text-left eds-type-small ${
                    level === item.id
                      ? "border-[var(--eds-primary)] bg-[var(--eds-primary-soft)]"
                      : "border-[var(--eds-border)]"
                  }`}
                  onClick={() => void loadLevel(item.id)}
                >
                  <strong>{item.name}</strong>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{item.description}</p>
                </button>
              ))}
            </div>
          ) : null}

          {step === 1 ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {HELP_FIELDS.map((f) => (
                  <Button key={f} variant="secondary" onClick={() => void loadHelp(f)}>
                    {f.replace(/_/g, " ")}
                  </Button>
                ))}
              </div>
              {help ? (
                <Card title="Contextual Справка">
                  <ul className="space-y-1 eds-type-small">
                    {Object.entries(help)
                      .filter(([k]) => HELP_FIELDS.includes(k as (typeof HELP_FIELDS)[number]))
                      .map(([k, v]) => (
                        <li key={k}>
                          <strong>{k.replace(/_/g, " ")}:</strong> {String(v)}
                        </li>
                      ))}
                  </ul>
                </Card>
              ) : null}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-3">
              <Input value={question} onChange={(e) => setQuestion(e.target.value)} />
              <Button disabled={busy} onClick={() => void runGuide()}>
                Ask AI Guide
              </Button>
              {guide ? (
                <Card title="Interactive Coach">
                  <p className="eds-type-small">
                    {(guide.explain as { message?: string } | undefined)?.message}
                  </p>
                  <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
                    {(guide.warnings as { message?: string } | undefined)?.message}
                  </p>
                  {(guide.answer as { answer?: string } | undefined)?.answer ? (
                    <p className="mt-2 eds-type-small">
                      Answer: {(guide.answer as { answer?: string }).answer}
                    </p>
                  ) : null}
                </Card>
              ) : null}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {RECOMMENDATION_TYPES.map((t) => (
                  <Badge key={t}>{t}</Badge>
                ))}
              </div>
              <Button disabled={busy} onClick={() => void loadRecs()}>
                Load live recommendations
              </Button>
              {recs ? (
                <pre className="max-h-48 overflow-auto eds-type-caption">
                  {JSON.stringify(recs.items, null, 2)}
                </pre>
              ) : null}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="space-y-3">
              <Button disabled={busy} onClick={() => void loadLearning()}>
                Show learning path
              </Button>
              {learning ? (
                <div className="space-y-2">
                  <p className="eds-type-small">Tips: {(learning.tips as string[])?.[0]}</p>
                  <div className="flex flex-wrap gap-2">
                    {((learning.learning_path as { title?: string }[]) || []).map((p) => (
                      <Badge key={p.title}>{p.title}</Badge>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-3">
              <Button disabled={busy} onClick={() => void runAnalysis()}>
                Analyze current builder
              </Button>
              {analysis ? (
                <ul className="space-y-1 eds-type-small">
                  <li>Strengths: {(analysis.strengths as string[])?.join(", ")}</li>
                  <li>Missing: {(analysis.missing_components as string[])?.join(", ") || "—"}</li>
                  <li>Score: {String(analysis.readiness_score)}</li>
                </ul>
              ) : null}
            </div>
          ) : null}

          {step === 6 ? (
            <div className="space-y-3">
              <Button disabled={busy} onClick={() => void loadImpact()}>
                Show business impact for CRM
              </Button>
              {impact ? (
                <Card title="Карточка бизнес-эффекта">
                  <ul className="space-y-1 eds-type-small">
                    <li>Value: {String(impact.business_value)}</li>
                    <li>Benefits: {String(impact.expected_benefits)}</li>
                    <li>Usage: {String(impact.typical_industry_usage)}</li>
                    <li>Impact: {String(impact.estimated_impact)}</li>
                  </ul>
                </Card>
              ) : null}
            </div>
          ) : null}

          {step === 7 ? (
            <div className="space-y-3">
              <Button disabled={busy} onClick={() => void loadProgress()}>
                Обновить progress timeline
              </Button>
              {progress ? (
                <div className="space-y-2">
                  <p className="eds-type-small">
                    Level: {String(progress.experience_level)} · XP: {String(progress.xp)}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {((progress.achievements as string[]) || []).map((a) => (
                      <Badge key={a}>{a}</Badge>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {step === 8 ? (
            <Card title="Итоги академии">
              <ul className="space-y-1 eds-type-small">
                <li>Configuration: level {level}</li>
                <li>Recommendations: {recs ? "loaded" : "pending"}</li>
                <li>Learning progress: {progress ? `${progress.xp} XP` : "pending"}</li>
                <li>
                  Business readiness:{" "}
                  {analysis ? String(analysis.readiness_score) : "run analysis"}
                </li>
              </ul>
            </Card>
          ) : null}

          {step === 9 ? (
            <div className="space-y-3">
              {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
              {created ? (
                <Card title="Registered">
                  <p className="eds-type-small">
                    Academy progress, recommendations, and learning state registered.
                  </p>
                  <pre className="mt-2 max-h-40 overflow-auto eds-type-caption">
                    {JSON.stringify(created.progress, null, 2)}
                  </pre>
                </Card>
              ) : (
                <Button variant="primary" disabled={busy} onClick={() => void syncAndCreate()}>
                  {busy ? "Saving…" : "Зарегистрировать прогресс академии"}
                </Button>
              )}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
              Назад
            </Button>
            <Button
              disabled={step >= ACADEMY_V2_STEPS.length - 1}
              onClick={() => setStep((s) => Math.min(ACADEMY_V2_STEPS.length - 1, s + 1))}
            >
              Далее
            </Button>
          </div>
        </Card>

        <HelpPanel help={panelHelp} guided={guided} />

        <Card title="Achievement Cards">
          <div className="flex flex-wrap gap-2">
            <Badge>First Builder</Badge>
            <Badge>Guided Learner</Badge>
            <Badge>AI Coach User</Badge>
            <Badge>Optimizer</Badge>
            <Badge>Business Ready</Badge>
          </div>
          <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
            Animated guidance and progress timeline unlock as you learn.
          </p>
        </Card>
      </div>
    </PlatformBuilderLayout>
  );
}
