import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { DEPARTMENTS, LIVE_STATUSES, TEAM_MAP_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function TeamMapStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [map, setMap] = useState<Dict | null>(null);
  const [cards, setCards] = useState<Dict | null>(null);
  const [live, setLive] = useState<Dict | null>(null);
  const [workload, setWorkload] = useState<Dict | null>(null);
  const [rels, setRels] = useState<Dict | null>(null);
  const [activity, setActivity] = useState<Dict | null>(null);
  const [events, setEvents] = useState<Dict | null>(null);
  const [visuals, setVisuals] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: TEAM_MAP_STEPS[step],
      detailedExplanation:
        "Live Organization Map visualizes the AI Organization in real time via the Visual Event Bus and Visual Layer.",
      example: `Example: complete «${TEAM_MAP_STEPS[step]}».`,
      popup: { title: TEAM_MAP_STEPS[step], body: "Interactive org map with zoom, pan, and filters." },
      tooltip: TEAM_MAP_STEPS[step],
      purpose: "See every AI object and connection live",
      benefits: "Operators understand hierarchy, workload, and relationships instantly",
      typicalUse: "Department focus during collaborative sessions",
      businessValue: "Foundation for AI City movement and animation",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/team-map/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/team-map/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: next + 1,
          draft: { department: department || null, search, focus_status: statusFilter || null },
        }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Navigation failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadMap() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const q = new URLSearchParams();
      if (department) q.set("department", department);
      if (search) q.set("search", search);
      if (statusFilter) q.set("status", statusFilter);
      const res = await fetch(`${PLATFORM_BUILDER_API}/team-map/map?${q}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Map failed");
      setMap(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Map failed");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/team-map/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function subscribeBus() {
    setBusy(true);
    try {
      await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/team-map/events/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channels: ["AI Events", "Task Events", "Organization Events"] }),
      });
      const poll = await fetch(`${PLATFORM_BUILDER_API}/team-map/events/poll`);
      setEvents(await poll.json());
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/team-map/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/team-map/sessions/${sid}/create`, {
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

  useEffect(() => {
    if (step === 0 && !map) void loadMap();
  }, [step]);

  const nodes = ((map?.nodes as Dict[]) || []);
  const edges = ((map?.edges as Dict[]) || []);

  function onPointerDown(e: ReactPointerEvent) {
    drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
  }
  function onPointerMove(e: ReactPointerEvent) {
    if (!drag.current) return;
    setPan({
      x: drag.current.px + (e.clientX - drag.current.x),
      y: drag.current.py + (e.clientY - drag.current.y),
    });
  }
  function onPointerUp() {
    drag.current = null;
  }

  return (
    <PlatformBuilderLayout
      title="AI Team Map"
      subtitle="Live Organization Map — Visual Event Bus, relationships, workload, and animation layer."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Live Organization</Badge>
        <Badge>Visual Event Bus</Badge>
        <Badge>Sprint 29.2</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={TEAM_MAP_STEPS.length} />
      <BuilderStepNav steps={[...TEAM_MAP_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Live Organization Map">
              <div className="mb-3 flex flex-wrap gap-2">
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search"
                />
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                >
                  <option value="">All departments</option>
                  {DEPARTMENTS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  {LIVE_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <Button disabled={busy} onClick={() => void loadMap()}>
                  Apply filters
                </Button>
                <Button variant="ghost" onClick={() => setZoom((z) => Math.min(2, z + 0.1))}>
                  Zoom +
                </Button>
                <Button variant="ghost" onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}>
                  Zoom −
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setZoom(1);
                    setPan({ x: 0, y: 0 });
                  }}
                >
                  Reset view
                </Button>
              </div>
              <div
                className="relative h-[420px] overflow-hidden rounded-md border border-[var(--eds-border)] bg-[radial-gradient(circle_at_30%_20%,rgba(56,189,248,0.08),transparent_40%),radial-gradient(circle_at_70%_70%,rgba(52,211,153,0.08),transparent_45%)]"
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                onPointerLeave={onPointerUp}
              >
                <div
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: "0 0",
                    width: 900,
                    height: 600,
                    position: "relative",
                  }}
                >
                  <svg className="absolute inset-0 h-full w-full" aria-hidden>
                    {edges.slice(0, 60).map((e, i) => {
                      const from = nodes.find((n) => n.logical_id === e.from);
                      const to = nodes.find((n) => n.logical_id === e.to);
                      if (!from || !to) return null;
                      const x1 = Number((from.current_position as Dict)?.x || 0);
                      const y1 = Number((from.current_position as Dict)?.y || 0);
                      const x2 = Number((to.current_position as Dict)?.x || 0);
                      const y2 = Number((to.current_position as Dict)?.y || 0);
                      return (
                        <line
                          key={i}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke="var(--eds-accent, #38bdf8)"
                          strokeWidth="1.25"
                          opacity="0.45"
                        >
                          <animate
                            attributeName="opacity"
                            values="0.2;0.65;0.2"
                            dur="2.8s"
                            repeatCount="indefinite"
                          />
                        </line>
                      );
                    })}
                  </svg>
                  {nodes.map((n) => {
                    const pos = (n.current_position as Dict) || {};
                    return (
                      <button
                        key={String(n.logical_id)}
                        type="button"
                        className="absolute -translate-x-1/2 -translate-y-1/2 rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface,rgba(0,0,0,0.45))] px-2 py-1 text-left eds-type-caption backdrop-blur"
                        style={{
                          left: Number(pos.x || 0),
                          top: Number(pos.y || 0),
                          animation: "cardPulse 2.4s ease infinite",
                        }}
                        onClick={() => setSearch(String(n.name))}
                      >
                        <div className="opacity-60">{String(n.object_type)}</div>
                        <div>{String(n.name)}</div>
                        <div className="opacity-70">{String(n.current_status)}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="AI Cards">
              <Button disabled={busy} onClick={() => void load("cards", setCards)}>
                Load AI cards
              </Button>
              {cards ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {((cards.cards as Dict[]) || []).map((c) => (
                    <div
                      key={String(c.logical_id)}
                      className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small animate-[fadeIn_0.35s_ease]"
                    >
                      <div className="font-medium">
                        {String(c.avatar)} · {String(c.name)}
                      </div>
                      <div>
                        {String(c.role)} · {String(c.specialization)} · {String(c.department)}
                      </div>
                      <div>
                        {String(c.current_status)} · {String(c.current_task)}
                      </div>
                      <div>
                        Knowledge {String(c.knowledge_level)} · Health {String(c.health)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Live Status">
              <Button disabled={busy} onClick={() => void load("live-status", setLive)}>
                Snapshot
              </Button>
              {live ? (
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {Object.entries((live.counts as Dict) || {}).map(([k, v]) => (
                    <div key={k} className="rounded-md border border-[var(--eds-border)] p-2 eds-type-small">
                      {k}: {String(v)}
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Workload Engine">
              <Button disabled={busy} onClick={() => void load("workload", setWorkload)}>
                Load workload
              </Button>
              {workload ? (
                <div className="mt-3 eds-type-small space-y-2">
                  <div>
                    Average load {String(workload.average_load)} · Balanced{" "}
                    {String(workload.balanced)}
                  </div>
                  <ul className="space-y-1">
                    {((workload.cards as Dict[]) || []).slice(0, 8).map((c) => (
                      <li key={String(c.logical_id)}>
                        {String(c.name)} — {JSON.stringify(c.workload)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Relationship Map">
              <Button disabled={busy} onClick={() => void load("relationships", setRels)}>
                Load relationships
              </Button>
              {rels ? (
                <ul className="mt-3 max-h-64 space-y-1 overflow-auto eds-type-small">
                  {((rels.edges as Dict[]) || []).slice(0, 40).map((e, i) => (
                    <li key={i}>
                      {String(e.from)} → {String(e.to)} · {String(e.category)} ({String(e.relation)})
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Live Activity">
              <Button disabled={busy} onClick={() => void load("activity", setActivity)}>
                Load activity
              </Button>
              {activity ? (
                <div className="mt-3 space-y-2 eds-type-small">
                  {Object.entries((activity.channels as Dict) || {}).map(([k, items]) => (
                    <div key={k}>
                      <div className="opacity-70">{k}</div>
                      <ul>
                        {((items as Dict[]) || []).map((it, i) => (
                          <li key={i}>
                            {String(it.actor)} — {String(it.detail)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Visual Event Bus">
              <Button disabled={busy} onClick={() => void subscribeBus()}>
                Subscribe & poll
              </Button>
              {events ? (
                <ul className="mt-3 max-h-64 space-y-1 overflow-auto eds-type-small">
                  {((events.events as Dict[]) || []).map((e) => (
                    <li key={String(e.event_id)}>
                      {String(e.channel)} · {String(e.event_type)} · {String(e.published_at)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Visual Objects">
              <Button disabled={busy} onClick={() => void load("visual-objects", setVisuals)}>
                List visual objects
              </Button>
              {visuals ? (
                <pre className="mt-3 max-h-72 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(((visuals.objects as Dict[]) || []).slice(0, 4), null, 2)}
                </pre>
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
            <Card title="Create — Register Map Engines">
              <p className="eds-type-small mb-3">
                Registers Organization Map, Relationship Engine, Workload Engine, and Animation Layer.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(created.registrations || {
                    organization_map_id: (created.organization_map as Dict)?.organization_map_id,
                    relationship_engine_id: (created.relationship_engine as Dict)?.relationship_engine_id,
                    workload_engine_id: (created.workload_engine as Dict)?.workload_engine_id,
                    animation_layer_id: (created.animation_layer as Dict)?.animation_layer_id,
                  }, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Back
            </Button>
            <Button
              disabled={busy || step >= TEAM_MAP_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Next
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        @keyframes cardPulse { 0%,100% { border-color: var(--eds-border); } 50% { border-color: var(--eds-accent, #38bdf8); } }
      `}</style>
    </PlatformBuilderLayout>
  );
}
