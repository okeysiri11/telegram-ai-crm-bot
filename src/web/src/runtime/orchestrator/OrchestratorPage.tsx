/**
 * Orchestrator dashboard — Sprint 29.8 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { enterpriseOrchestrator } from "@/runtime/orchestrator";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "runtimes" | "health" | "graph" | "queue" | "events";

export function OrchestratorPage() {
  const [tab, setTab] = useState<Tab>("runtimes");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return enterpriseOrchestrator.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Orchestrator Runtime · ADOS";
    rememberModuleRoute("/orchestrator");
    enterpriseOrchestrator.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 4000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    enterpriseOrchestrator.platformHealth();
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "runtimes", label: "Runtimes" },
    { id: "health", label: "Health" },
    { id: "graph", label: "Dependency Graph" },
    { id: "queue", label: "Queue" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Orchestrator</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.runtimes} runtimes · platform{" "}
            {snap.health.status} · {snap.health.healthy}/{snap.health.total} healthy
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={refresh}>
            Probe Health
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              enterpriseOrchestrator.schedule("refresh", "intelligence");
              refresh();
            }}
          >
            Refresh Intelligence
          </Button>
          <Link to="/intelligence" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Intel →
          </Link>
          <Link to="/interactions" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Interact →
          </Link>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button
            key={t.id}
            size="sm"
            variant={tab === t.id ? "primary" : "ghost"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "runtimes" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.runtimes.map((r) => (
            <Card key={r.id} title={r.label}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{r.status}</Badge>
                <Badge>v{r.version}</Badge>
              </div>
              <p className="eds-type-helper">
                deps: {r.dependencies.join(" → ") || "—"} · api {r.api}
              </p>
              {r.route ? (
                <Link to={r.route} className="eds-type-small text-[var(--eds-primary)]">
                  Open →
                </Link>
              ) : null}
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "health" ? (
        <Card title="Platform Health">
          <ul className="eds-type-small space-y-1">
            <li>Status: {snap.health.status}</li>
            <li>Healthy: {snap.health.healthy}</li>
            <li>Starting: {snap.health.starting}</li>
            <li>Busy: {snap.health.busy}</li>
            <li>Error: {snap.health.error}</li>
            <li>Stopped: {snap.health.stopped}</li>
            <li>Maintenance: {snap.health.maintenance}</li>
          </ul>
        </Card>
      ) : null}

      {tab === "graph" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Startup Order">
            <ol className="eds-type-small list-decimal pl-4 space-y-1">
              {snap.order.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ol>
          </Card>
          <Card title="Canonical Chain">
            <p className="eds-type-small">{snap.canonicalChain.join(" → ")}</p>
            <ul className="eds-type-helper mt-3 space-y-1">
              {snap.edges.slice(0, 24).map((e, i) => (
                <li key={`${e.from}-${e.to}-${i}`}>
                  {e.from} → {e.to}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "queue" ? (
        <Card title="Scheduler Queue">
          <ul className="eds-type-small space-y-1">
            {snap.queue.map((j) => (
              <li key={j.id}>
                {j.enqueuedAt.slice(11, 19)} · {j.operation}
                {j.runtimeId ? ` · ${j.runtimeId}` : " · platform"} · <Badge>{j.status}</Badge>
              </li>
            ))}
            {!snap.queue.length ? <li className="eds-type-helper">Queue empty</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "events" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Routed Bus Events">
            <ul className="eds-type-small space-y-1">
              {snap.routedEvents.map((e) => (
                <li key={e.id}>
                  {e.at.slice(11, 19)} · {e.busType} → {e.targetRuntimeIds.join(", ") || "—"}
                </li>
              ))}
              {!snap.routedEvents.length ? (
                <li className="eds-type-helper">No routed events yet</li>
              ) : null}
            </ul>
          </Card>
          <Card title="Orchestrator Events">
            <ul className="eds-type-small space-y-1">
              {snap.events.map((e) => (
                <li key={e.id}>
                  {e.at.slice(11, 19)} · {e.name}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      ) : null}
    </FullLayout>
  );
}
