import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { WORKSPACE_OS_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function WorkspaceOSStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [types, setTypes] = useState<Dict | null>(null);
  const [layout, setLayout] = useState<Dict | null>(null);
  const [session, setSession] = useState<Dict | null>(null);
  const [modules, setModules] = useState<Dict | null>(null);
  const [context, setContext] = useState<Dict | null>(null);
  const [multitasking, setMultitasking] = useState<Dict | null>(null);
  const [search, setSearch] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [selectedType, setSelectedType] = useState("Manager Workspace");
  const [query, setQuery] = useState("AI");

  const panelHelp = useMemo(
    () => ({
      shortDescription: WORKSPACE_OS_STEPS[step],
      detailedExplanation:
        "ОС рабочего пространства is the unified operating environment for every platform module. It provides one consistent workspace while allowing each department, AI team and application to keep its own context.",
      example: `Example: complete «${WORKSPACE_OS_STEPS[step]}».`,
      popup: { title: WORKSPACE_OS_STEPS[step], body: "Unified workspace platform." },
      tooltip: WORKSPACE_OS_STEPS[step],
      purpose: "Unified multi-workspace operating environment",
      benefits: "Layouts, sessions, context, search, and performance",
      typicalUse: "Workspace Launcher and Layout Editor",
      businessValue: "One OS shell for every module without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/workspace-os/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/workspace-os/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/workspace-os/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function applyType() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/workspace-os/types`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: selectedType }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка обновления типа");
      setTypes(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка обновления типа");
    } finally {
      setBusy(false);
    }
  }

  async function runSearch() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/workspace-os/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка поиска");
      setSearch(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка поиска");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/workspace-os/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: 10,
          draft: { workspace_type: selectedType },
        }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/workspace-os/sessions/${sid}/create`, {
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
      title="ОС рабочего пространства"
      subtitle="Unified workspace platform — multi-workspace, role aware, high performance."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Multi Workspace</Badge>
        <Badge>Role Aware</Badge>
        <Badge>Layout Engine</Badge>
        <Badge>Sprint 29.12</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={WORKSPACE_OS_STEPS.length} />
      <BuilderStepNav steps={[...WORKSPACE_OS_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Workspace OS Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load Workspace OS
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
            <Card title="Workspace Types">
              <div className="flex flex-wrap gap-2">
                <select
                  className="eds-input"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                >
                  {[
                    "Executive Workspace",
                    "Manager Workspace",
                    "Operator Workspace",
                    "Developer Workspace",
                    "Builder Workspace",
                    "Аналитика Workspace",
                    "Support Workspace",
                    "Организация Workspace",
                  ].map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void applyType()}>
                  Apply type
                </Button>
                <Button disabled={busy} onClick={() => void load("types", setTypes)}>
                  Обновить
                </Button>
              </div>
              {types ? (
                <p className="mt-3 eds-type-small">Active: {String(types.active_type)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Layout Engine">
              <Button disabled={busy} onClick={() => void load("layout", setLayout)}>
                Load layout
              </Button>
              {layout ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((layout.features as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Session Management">
              <Button disabled={busy} onClick={() => void load("session", setSession)}>
                Load session
              </Button>
              {session ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(session.session, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Module Integration">
              <Button disabled={busy} onClick={() => void load("modules", setModules)}>
                Load modules
              </Button>
              {modules ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((modules.modules as string[]) || []).map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Context Engine">
              <Button disabled={busy} onClick={() => void load("context", setContext)}>
                Load context
              </Button>
              {context ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((context.layers as string[]) || []).map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Multitasking">
              <Button disabled={busy} onClick={() => void load("multitasking", setMultitasking)}>
                Load multitasking
              </Button>
              {multitasking ? (
                <p className="mt-3 eds-type-small">
                  Workspaces: {((multitasking.workspaces as unknown[]) || []).length} · active{" "}
                  {String(multitasking.active_workspace_id)}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Workspace Поиск">
              <div className="flex flex-wrap gap-2">
                <input
                  className="eds-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Поиск modules, types, commands"
                />
                <Button disabled={busy} onClick={() => void runSearch()}>
                  Search
                </Button>
              </div>
              {search ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {(((search.results as Dict[]) || []) as Dict[]).map((r, i) => (
                    <li key={`${String(r.title)}-${i}`}>
                      {String(r.scope)}: {String(r.title)}
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
                  Load Workspace UI
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
                Register Workspace OS
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    workspace_os_id: {(created.workspace_os as Dict)?.workspace_os_id as string}
                  </li>
                  <li>
                    workspace_registry_id:{" "}
                    {(created.workspace_registry as Dict)?.workspace_registry_id as string}
                  </li>
                  <li>
                    layout_engine_id: {(created.layout_engine as Dict)?.layout_engine_id as string}
                  </li>
                  <li>
                    context_engine_id:{" "}
                    {(created.context_engine as Dict)?.context_engine_id as string}
                  </li>
                  <li>
                    session_manager_id:{" "}
                    {(created.session_manager as Dict)?.session_manager_id as string}
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
