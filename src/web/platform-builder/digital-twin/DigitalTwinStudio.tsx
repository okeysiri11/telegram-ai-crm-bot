import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { DIGITAL_TWIN_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function DigitalTwinStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [organization, setOrganization] = useState<Dict | null>(null);
  const [ai, setAi] = useState<Dict | null>(null);
  const [workflow, setWorkflow] = useState<Dict | null>(null);
  const [knowledge, setKnowledge] = useState<Dict | null>(null);
  const [resources, setResources] = useState<Dict | null>(null);
  const [snapshots, setSnapshots] = useState<Dict | null>(null);
  const [comparison, setComparison] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: DIGITAL_TWIN_STEPS[step],
      detailedExplanation:
        "Цифровой двойник предприятия mirrors verified platform state in realtime. It never owns business logic — it is a read-only reflection layer aggregating existing services.",
      example: `Example: complete «${DIGITAL_TWIN_STEPS[step]}».`,
      popup: { title: DIGITAL_TWIN_STEPS[step], body: "Организация and platform mirror." },
      tooltip: DIGITAL_TWIN_STEPS[step],
      purpose: "Realtime verified-state reflection",
      benefits: "Организация, AI, workflow, knowledge and resource mirrors",
      typicalUse: "Digital Twin Center and Snapshot Browser",
      businessValue: "Shared situational awareness without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/digital-twin/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/digital-twin/sessions/${sid}`, {
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/digital-twin/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function captureSnapshot() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/digital-twin/snapshots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "capture", type: "Realtime Snapshot" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Snapshot failed");
      setSnapshots(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Snapshot failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/digital-twin/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/digital-twin/sessions/${sid}/create`, {
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
      title="Цифровой двойник предприятия"
      subtitle="Read-only realtime mirror of verified platform state — never owns business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Read-Only</Badge>
        <Badge>Realtime</Badge>
        <Badge>Verified State</Badge>
        <Badge>Sprint 29.16</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={DIGITAL_TWIN_STEPS.length} />
      <BuilderStepNav steps={[...DIGITAL_TWIN_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Digital Twin Core">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load twin engine
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
            <Card title="Организация Mirror">
              <Button disabled={busy} onClick={() => void load("organization", setOrganization)}>
                Load organization mirror
              </Button>
              {organization ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((organization.entities as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="AI Mirror">
              <Button disabled={busy} onClick={() => void load("ai", setAi)}>
                Load AI mirror
              </Button>
              {ai ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((ai.entities as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Сценарий Mirror">
              <Button disabled={busy} onClick={() => void load("workflow", setWorkflow)}>
                Load workflow mirror
              </Button>
              {workflow ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((workflow.entities as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="База знаний Mirror">
              <Button disabled={busy} onClick={() => void load("knowledge", setKnowledge)}>
                Load knowledge mirror
              </Button>
              {knowledge ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((knowledge.entities as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Resource Mirror">
              <Button disabled={busy} onClick={() => void load("resources", setResources)}>
                Load resource mirror
              </Button>
              {resources ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((resources.entities as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Snapshot Engine">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("snapshots", setSnapshots)}>
                  Browse snapshots
                </Button>
                <Button disabled={busy} onClick={() => void captureSnapshot()}>
                  Capture realtime snapshot
                </Button>
              </div>
              {snapshots ? (
                <p className="mt-3 eds-type-small">
                  Snapshots: {((snapshots.snapshots as unknown[]) || []).length}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="State Comparison">
              <Button disabled={busy} onClick={() => void load("comparison", setComparison)}>
                Load comparisons
              </Button>
              {comparison ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((comparison.dimensions as string[]) || []).map((d) => (
                    <li key={d}>{d}</li>
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
                  Load Twin UI
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
                Register Digital Twin
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    digital_twin_engine_id:{" "}
                    {(created.digital_twin_engine as Dict)?.digital_twin_engine_id as string}
                  </li>
                  <li>
                    twin_registry_id: {(created.twin_registry as Dict)?.twin_registry_id as string}
                  </li>
                  <li>
                    synchronization_engine_id:{" "}
                    {(created.synchronization_engine as Dict)?.synchronization_engine_id as string}
                  </li>
                  <li>
                    snapshot_engine_id:{" "}
                    {(created.snapshot_engine as Dict)?.snapshot_engine_id as string}
                  </li>
                  <li>twin_api_id: {(created.twin_api as Dict)?.twin_api_id as string}</li>
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
