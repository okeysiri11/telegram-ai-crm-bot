import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { COMMAND_CENTER_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function CommandCenterStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [palette, setPalette] = useState<Dict | null>(null);
  const [execution, setExecution] = useState<Dict | null>(null);
  const [categories, setCategories] = useState<Dict | null>(null);
  const [voice, setVoice] = useState<Dict | null>(null);
  const [hotkeys, setHotkeys] = useState<Dict | null>(null);
  const [history, setHistory] = useState<Dict | null>(null);
  const [assistant, setAssistant] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [query, setQuery] = useState("AI");
  const [utterance, setUtterance] = useState("open analytics");

  const panelHelp = useMemo(
    () => ({
      shortDescription: COMMAND_CENTER_STEPS[step],
      detailedExplanation:
        "Центр управления is the universal control layer for the platform. It orchestrates user interaction across modules, AI agents, workspaces and services — never business logic.",
      example: `Example: complete «${COMMAND_CENTER_STEPS[step]}».`,
      popup: { title: COMMAND_CENTER_STEPS[step], body: "Universal command platform." },
      tooltip: COMMAND_CENTER_STEPS[step],
      purpose: "Universal command interface",
      benefits: "Palette, hotkeys, voice foundation, AI suggestions",
      typicalUse: "Command Palette and Quick Launcher",
      businessValue: "One interaction layer without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/command-center/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function runPalette() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/palette`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Palette failed");
      setPalette(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Palette failed");
    } finally {
      setBusy(false);
    }
  }

  async function runExecute(commandId: string) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command_id: commandId }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Execute failed");
      setExecution(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execute failed");
    } finally {
      setBusy(false);
    }
  }

  async function runAssistant() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ utterance }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Assistant failed");
      setAssistant(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assistant failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/command-center/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/command-center/sessions/${sid}/create`, {
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
      title="Центр управления"
      subtitle="Universal command platform — keyboard first, voice ready, AI native. Interaction only."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">No Business Logic</Badge>
        <Badge>Keyboard First</Badge>
        <Badge>Voice Ready</Badge>
        <Badge>AI Native</Badge>
        <Badge>Sprint 29.13</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={COMMAND_CENTER_STEPS.length} />
      <BuilderStepNav
        steps={[...COMMAND_CENTER_STEPS]}
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
            <Card title="Command Center Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load Command Center
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
            <Card title="Global Command Palette">
              <div className="flex flex-wrap gap-2">
                <input
                  className="eds-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Universal search"
                />
                <Button disabled={busy} onClick={() => void runPalette()}>
                  Search
                </Button>
              </div>
              {palette ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {(((palette.results as Dict[]) || []) as Dict[]).map((r) => (
                    <li key={String(r.id)}>
                      {String(r.title)} · {String(r.category)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Command Execution">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("execute", setExecution)}>
                  Load execution types
                </Button>
                <Button disabled={busy} onClick={() => void runExecute("cmd_open_ops")}>
                  Dispatch Open Ops
                </Button>
              </div>
              {execution ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(execution.execution || execution.execution_types, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Command Categories">
              <Button disabled={busy} onClick={() => void load("categories", setCategories)}>
                Load categories
              </Button>
              {categories ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((categories.categories as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Voice Foundation">
              <Button disabled={busy} onClick={() => void load("voice", setVoice)}>
                Load voice APIs
              </Button>
              {voice ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((voice.apis as string[]) || []).map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Hotkey Engine">
              <Button disabled={busy} onClick={() => void load("hotkeys", setHotkeys)}>
                Load shortcuts
              </Button>
              {hotkeys ? (
                <pre className="mt-3 overflow-auto eds-type-small">
                  {JSON.stringify(hotkeys.shortcuts, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Command History">
              <Button disabled={busy} onClick={() => void load("history", setHistory)}>
                Load history
              </Button>
              {history ? (
                <p className="mt-3 eds-type-small">
                  History: {((history.history as unknown[]) || []).length} · Favorites{" "}
                  {((history.favorites as unknown[]) || []).length}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="AI Command Assistant">
              <div className="flex flex-wrap gap-2">
                <input
                  className="eds-input"
                  value={utterance}
                  onChange={(e) => setUtterance(e.target.value)}
                  placeholder="Natural language command"
                />
                <Button disabled={busy} onClick={() => void runAssistant()}>
                  Suggest
                </Button>
              </div>
              {assistant ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {(((assistant.suggestions as Dict[]) || []) as Dict[]).map((s) => (
                    <li key={String(s.id)}>{String(s.title)}</li>
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
                  Load Command UI
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
                Register Command Center
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    command_center_id:{" "}
                    {(created.command_center as Dict)?.command_center_id as string}
                  </li>
                  <li>
                    command_registry_id:{" "}
                    {(created.command_registry as Dict)?.command_registry_id as string}
                  </li>
                  <li>
                    command_api_id: {(created.command_api as Dict)?.command_api_id as string}
                  </li>
                  <li>
                    shortcut_engine_id:{" "}
                    {(created.shortcut_engine as Dict)?.shortcut_engine_id as string}
                  </li>
                  <li>voice_api_id: {(created.voice_api as Dict)?.voice_api_id as string}</li>
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
