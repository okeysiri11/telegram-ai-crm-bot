import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import {
  CONTROL_CENTER_SURFACES,
  GOD_CAPABILITIES,
  OWNER_HEADERS,
} from "../managers/godMode";
import { PLATFORM_BUILDER_API } from "../types";
import { CONTROL_CENTER_STEPS, REGISTRY_ACTIONS, SEARCH_SCOPES } from "./catalog";

type Dict = Record<string, unknown>;

export function ControlCenterStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Dict | null>(null);
  const [query, setQuery] = useState("seed");
  const [scope, setScope] = useState("AI");
  const [search, setSearch] = useState<Dict | null>(null);
  const [objectId, setObjectId] = useState("ai_seed");
  const [inspected, setInspected] = useState<Dict | null>(null);
  const [editMeta, setEditMeta] = useState('{"note":"control-center"}');
  const [edited, setEdited] = useState<Dict | null>(null);
  const [registries, setRegistries] = useState<Dict | null>(null);
  const [registryAction, setRegistryAction] = useState("Synchronize");
  const [health, setHealth] = useState<Dict | null>(null);
  const [diagnostics, setDiagnostics] = useState<Dict | null>(null);
  const [architecture, setArchitecture] = useState<Dict | null>(null);
  const [audit, setAudit] = useState<Dict | null>(null);
  const [recommendation, setRecommendation] = useState("Synchronize registries");
  const [explain, setExplain] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: CONTROL_CENTER_STEPS[step],
      detailedExplanation:
        "Режим владельца Центр управления платформой gives the Platform Owner unrestricted access to every object, registry, and architecture surface.",
      example: `Example: complete «${CONTROL_CENTER_STEPS[step]}».`,
      popup: {
        title: CONTROL_CENTER_STEPS[step],
        body: "Enterprise Platform Control — owner only.",
      },
      tooltip: CONTROL_CENTER_STEPS[step],
      purpose: "Enterprise Центр управления платформой",
      benefits: "Full visibility, diagnostics, and repair in one place",
      typicalUse: "Platform Owner incident response and architecture review",
      businessValue: "Faster recovery and safer platform evolution",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/sessions`, {
      method: "POST",
      headers: OWNER_HEADERS,
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать Control Center session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/sessions/${sid}`, {
        method: "PATCH",
        headers: OWNER_HEADERS,
        body: JSON.stringify({
          step: next + 1,
          draft: {
            search_query: query,
            focus_object_id: objectId,
            registry_action: registryAction,
            recommendation,
          },
        }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка навигации");
    } finally {
      setBusy(false);
    }
  }

  async function loadOverview() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/overview`, {
        headers: OWNER_HEADERS,
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка обзора");
      setOverview(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка обзора");
    } finally {
      setBusy(false);
    }
  }

  async function runSearch() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/god-mode/control/search?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}`,
        { headers: OWNER_HEADERS },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка поиска");
      setSearch(body);
      const first = (body.results as Dict[] | undefined)?.[0];
      if (first?.internal_id) setObjectId(String(first.internal_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка поиска");
    } finally {
      setBusy(false);
    }
  }

  async function runInspect() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/god-mode/control/objects/${encodeURIComponent(objectId)}`,
        { headers: OWNER_HEADERS },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Inspect failed");
      setInspected(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Inspect failed");
    } finally {
      setBusy(false);
    }
  }

  async function runEdit() {
    setBusy(true);
    setError(null);
    try {
      let metadata: unknown = editMeta;
      try {
        metadata = JSON.parse(editMeta);
      } catch {
        metadata = { note: editMeta };
      }
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/god-mode/control/objects/${encodeURIComponent(objectId)}`,
        {
          method: "PATCH",
          headers: OWNER_HEADERS,
          body: JSON.stringify({ metadata, properties: { edited_via: "control_center" } }),
        },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Edit failed");
      setEdited(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Edit failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadRegistries(action?: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/registries`, {
        method: "POST",
        headers: OWNER_HEADERS,
        body: JSON.stringify({ action: action || registryAction }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Реестры failed");
      setRegistries(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Реестры failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadHealth() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/health`, {
        headers: OWNER_HEADERS,
      });
      setHealth(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadDiagnostics() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/diagnostics`, {
        headers: OWNER_HEADERS,
      });
      setDiagnostics(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadArchitecture() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/architecture`, {
        headers: OWNER_HEADERS,
      });
      setArchitecture(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadAudit() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/audit`, {
        headers: OWNER_HEADERS,
      });
      setAudit(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runExplain() {
    setBusy(true);
    try {
      const res = await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/explain`, {
        method: "POST",
        headers: OWNER_HEADERS,
        body: JSON.stringify({ recommendation }),
      });
      setExplain(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/god-mode/control/sessions/${sid}`, {
        method: "PATCH",
        headers: OWNER_HEADERS,
        body: JSON.stringify({
          step: 11,
          draft: { recommendation, focus_object_id: objectId },
        }),
      });
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/god-mode/control/sessions/${sid}/create`,
        { method: "POST", headers: OWNER_HEADERS, body: "{}" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка создания");
      setCreated(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    } finally {
      setBusy(false);
    }
  }

  const nodes = (architecture?.nodes as Dict[] | undefined) || [];
  const edges = (architecture?.edges as Dict[] | undefined) || [];

  return (
    <PlatformBuilderLayout
      title="Режим владельца · Центр управления платформой"
      subtitle="Enterprise Platform Control — Platform Owner only."
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Platform Owner</Badge>
        <Badge>Режим владельца 2.0</Badge>
        <Badge>Sprint 28.7</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={CONTROL_CENTER_STEPS.length} />
      <BuilderStepNav
        steps={[...CONTROL_CENTER_STEPS]}
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
            <Card title="Global Platform Обзор">
              <p className="eds-type-small mb-3">
                Organizations · Users · AI · Concierges · Verticals · Departments · Modules ·
                Knowledge · Workflows · Маркетплейс · Registries · Visual Layer
              </p>
              <Button disabled={busy} onClick={() => void loadOverview()}>
                Load overview
              </Button>
              {overview ? (
                <div className="mt-4 grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {Object.entries((overview.categories as Dict) || {}).map(([k, v]) => (
                    <div
                      key={k}
                      className="rounded-md border border-[var(--eds-border)] p-3 transition hover:border-[var(--eds-accent)] animate-[fadeIn_0.4s_ease]"
                    >
                      <div className="eds-type-caption opacity-70">{k}</div>
                      <div className="eds-type-title">{String(v)}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Global Поиск">
              <div className="flex flex-wrap gap-2">
                <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Query" />
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                >
                  {SEARCH_SCOPES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void runSearch()}>
                  Search
                </Button>
              </div>
              {search ? (
                <ul className="mt-3 space-y-1 eds-type-small">
                  {((search.results as Dict[]) || []).map((r) => (
                    <li key={String(r.internal_id)}>
                      <button
                        type="button"
                        className="underline"
                        onClick={() => setObjectId(String(r.internal_id))}
                      >
                        {String(r.name)} · {String(r.object_type)} · {String(r.internal_id)}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Object Inspector">
              <div className="flex flex-wrap gap-2">
                <Input value={objectId} onChange={(e) => setObjectId(e.target.value)} />
                <Button disabled={busy} onClick={() => void runInspect()}>
                  Inspect
                </Button>
              </div>
              {inspected ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(inspected, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Live Object Editor">
              <p className="eds-type-small mb-2">Editing {objectId}</p>
              <Input value={editMeta} onChange={(e) => setEditMeta(e.target.value)} />
              <Button className="mt-2" disabled={busy} onClick={() => void runEdit()}>
                Apply edit
              </Button>
              {edited ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(edited, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Global Registry">
              <div className="flex flex-wrap gap-2">
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={registryAction}
                  onChange={(e) => setRegistryAction(e.target.value)}
                >
                  {REGISTRY_ACTIONS.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void loadRegistries()}>
                  Run action
                </Button>
              </div>
              {registries ? (
                <ul className="mt-3 space-y-1 eds-type-small">
                  {((registries.registries as Dict[]) || []).map((r) => (
                    <li key={String(r.name)}>
                      {String(r.name)} · {String(r.count)} · {String(r.status)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="System Health">
              <Button disabled={busy} onClick={() => void loadHealth()}>
                Обновить health
              </Button>
              {health ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {Object.entries((health.metrics as Dict) || {}).map(([k, v]) => {
                    const m = v as Dict;
                    return (
                      <div
                        key={k}
                        className="rounded-md border border-[var(--eds-border)] p-3 animate-[pulseSoft_2s_ease_infinite]"
                      >
                        <div className="font-medium">{k}</div>
                        <div className="eds-type-small">
                          {String(m.status)} — {String(m.detail)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Platform Diagnostics">
              <Button disabled={busy} onClick={() => void loadDiagnostics()}>
                Run diagnostics
              </Button>
              {diagnostics ? (
                <ul className="mt-3 space-y-2 eds-type-small">
                  {((diagnostics.findings as Dict[]) || []).map((f, i) => (
                    <li key={i} className="rounded-md border border-[var(--eds-border)] p-2">
                      <strong>{String(f.check)}</strong> [{String(f.severity)}] —{" "}
                      {String(f.message)}
                      {f.repair ? <div>Repair: {String(f.repair)}</div> : null}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Architecture Explorer">
              <Button disabled={busy} onClick={() => void loadArchitecture()}>
                Load architecture
              </Button>
              {architecture ? (
                <div className="mt-4 relative min-h-[220px] overflow-hidden rounded-md border border-[var(--eds-border)] bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.12),transparent_40%),radial-gradient(circle_at_80%_60%,rgba(52,211,153,0.1),transparent_45%)] p-4">
                  <svg className="absolute inset-0 h-full w-full" aria-hidden>
                    {edges.map((e, i) => {
                      const from = nodes.findIndex((n) => n.id === e.from);
                      const to = nodes.findIndex((n) => n.id === e.to);
                      if (from < 0 || to < 0) return null;
                      const x1 = 40 + (from % 4) * 120;
                      const y1 = 40 + Math.floor(from / 4) * 80;
                      const x2 = 40 + (to % 4) * 120;
                      const y2 = 40 + Math.floor(to / 4) * 80;
                      return (
                        <line
                          key={i}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke="var(--eds-accent, #38bdf8)"
                          strokeWidth="1.5"
                          opacity="0.55"
                        >
                          <animate
                            attributeName="opacity"
                            values="0.2;0.7;0.2"
                            dur="3s"
                            repeatCount="indefinite"
                          />
                        </line>
                      );
                    })}
                  </svg>
                  <div className="relative grid grid-cols-2 gap-3 md:grid-cols-4">
                    {nodes.map((n) => (
                      <div
                        key={String(n.id)}
                        className="rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface,rgba(0,0,0,0.35))] p-2 eds-type-caption backdrop-blur"
                      >
                        <div className="opacity-60">{String(n.kind)}</div>
                        <div>{String(n.label)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Audit Center">
              <Button disabled={busy} onClick={() => void loadAudit()}>
                Load audit
              </Button>
              {audit ? (
                <ul className="mt-3 max-h-64 space-y-1 overflow-auto eds-type-small">
                  {((audit.entries as Dict[]) || []).map((e) => (
                    <li key={String(e.audit_id)}>
                      {String(e.when)} · {String(e.who)} · {String(e.what)} → {String(e.target)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Explain Mode">
              <Input
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
              />
              <Button className="mt-2" disabled={busy} onClick={() => void runExplain()}>
                Explain recommendation
              </Button>
              {explain ? (
                <dl className="mt-3 space-y-2 eds-type-small">
                  <div>
                    <dt className="opacity-60">Reason</dt>
                    <dd>{String(explain.reason)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Expected Benefit</dt>
                    <dd>{String(explain.expected_benefit)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Business Impact</dt>
                    <dd>{String(explain.business_impact)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Alternatives</dt>
                    <dd>{((explain.alternative_options as string[]) || []).join(" · ")}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Estimated Effect</dt>
                    <dd>{String(explain.estimated_effect)}</dd>
                  </div>
                </dl>
              ) : null}
            </Card>
          ) : null}

          {step === 10 ? (
            <Card title="Создать — зарегистрировать Control Centers">
              <p className="eds-type-small mb-3">
                Registers Diagnostics, Audit, Architecture snapshot, and Health Center for the
                Platform Owner.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register centers
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(created.centers ?? created, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Назад
            </Button>
            <Button
              disabled={busy || step >= CONTROL_CENTER_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Далее
            </Button>
          </div>

          <Card title="Capabilities">
            <ul className="grid gap-2 md:grid-cols-2">
              {[...GOD_CAPABILITIES, ...CONTROL_CENTER_SURFACES].map((c) => (
                <li
                  key={c}
                  className="rounded-md border border-[var(--eds-border)] p-2 eds-type-small"
                >
                  {c.replaceAll("_", " ")}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <HelpPanel help={panelHelp} guided />
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        @keyframes pulseSoft { 0%,100% { border-color: var(--eds-border); } 50% { border-color: var(--eds-accent, #38bdf8); } }
      `}</style>
    </PlatformBuilderLayout>
  );
}
