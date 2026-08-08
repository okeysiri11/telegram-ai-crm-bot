import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { EXPERIENCE_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function ExperienceEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [unified, setUnified] = useState<Dict | null>(null);
  const [context, setContext] = useState<Dict | null>(null);
  const [adaptive, setAdaptive] = useState<Dict | null>(null);
  const [transitions, setTransitions] = useState<Dict | null>(null);
  const [rules, setRules] = useState<Dict | null>(null);
  const [cognitive, setCognitive] = useState<Dict | null>(null);
  const [workspaces, setWorkspaces] = useState<Dict | null>(null);
  const [accessibility, setAccessibility] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [selectedContext, setSelectedContext] = useState("Manager Context");

  const panelHelp = useMemo(
    () => ({
      shortDescription: EXPERIENCE_STEPS[step],
      detailedExplanation:
        "Движок визуального опыта unifies every visual subsystem into one seamless enterprise experience. It coordinates presentation, consistency, accessibility and user perception — never business logic.",
      example: `Example: complete «${EXPERIENCE_STEPS[step]}».`,
      popup: { title: EXPERIENCE_STEPS[step], body: "Unified enterprise UX coordination." },
      tooltip: EXPERIENCE_STEPS[step],
      purpose: "Unified presentation experience",
      benefits: "Adaptive UI, accessibility, cognitive load control",
      typicalUse: "Experience Center and UX diagnostics",
      businessValue: "Consistent enterprise perception without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/experience/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/experience/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/experience/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function applyContext() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/experience/context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context: selectedContext }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Context update failed");
      setContext(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Context update failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/experience/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: 10,
          draft: { context: selectedContext },
        }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/experience/sessions/${sid}/create`, {
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
      title="Движок визуального опыта"
      subtitle="Unified enterprise UX — presentation coordination only, no business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Logic</Badge>
        <Badge>Adaptive Interface</Badge>
        <Badge>Accessibility Ready</Badge>
        <Badge>Sprint 29.11</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={EXPERIENCE_STEPS.length} />
      <BuilderStepNav steps={[...EXPERIENCE_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Движок визуального опыта">
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
            <Card title="Unified Experience">
              <Button disabled={busy} onClick={() => void load("unified", setUnified)}>
                Load unified map
              </Button>
              {unified ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((unified.subsystem_names as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="User Context">
              <div className="flex flex-wrap gap-2">
                <select
                  className="eds-input"
                  value={selectedContext}
                  onChange={(e) => setSelectedContext(e.target.value)}
                >
                  {[
                    "Executive Context",
                    "Manager Context",
                    "Operator Context",
                    "Developer Context",
                    "Administrator Context",
                    "Guest Context",
                  ].map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void applyContext()}>
                  Apply context
                </Button>
                <Button disabled={busy} onClick={() => void load("context", setContext)}>
                  Обновить
                </Button>
              </div>
              {context ? (
                <p className="mt-3 eds-type-small">Active: {String(context.active_context)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Adaptive Interface">
              <Button disabled={busy} onClick={() => void load("adaptive", setAdaptive)}>
                Load adaptive profile
              </Button>
              {adaptive ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(adaptive.profile, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Transitions">
              <Button disabled={busy} onClick={() => void load("transitions", setTransitions)}>
                Load transitions
              </Button>
              {transitions ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((transitions.types as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Global Experience Rules">
              <Button disabled={busy} onClick={() => void load("rules", setRules)}>
                Load rules
              </Button>
              {rules ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((rules.rule_names as string[]) || []).map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Cognitive Load Control">
              <Button disabled={busy} onClick={() => void load("cognitive", setCognitive)}>
                Load cognitive controls
              </Button>
              {cognitive ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((cognitive.controls as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Multi-Workspace Experience">
              <Button disabled={busy} onClick={() => void load("workspaces", setWorkspaces)}>
                Load workspaces
              </Button>
              {workspaces ? (
                <p className="mt-3 eds-type-small">
                  Active workspace: {String(workspaces.active_workspace_id)} · count{" "}
                  {((workspaces.workspaces as unknown[]) || []).length}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Accessibility">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("accessibility", setAccessibility)}>
                  Load accessibility
                </Button>
                <Button disabled={busy} onClick={() => void load("ui", setUi)}>
                  Load Experience Center UI
                </Button>
              </div>
              {accessibility ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {Object.entries((accessibility.features as Dict) || {}).map(([k, v]) => (
                    <li key={k}>
                      {k}: {String(v)}
                    </li>
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
                Зарегистрировать движок опыта
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    experience_engine_id:{" "}
                    {(created.experience_engine as Dict)?.experience_engine_id as string}
                  </li>
                  <li>
                    experience_registry_id:{" "}
                    {(created.experience_registry as Dict)?.experience_registry_id as string}
                  </li>
                  <li>
                    ux_rules_registry_id:{" "}
                    {(created.ux_rules_registry as Dict)?.ux_rules_registry_id as string}
                  </li>
                  <li>
                    adaptive_ui_registry_id:{" "}
                    {(created.adaptive_ui_registry as Dict)?.adaptive_ui_registry_id as string}
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
