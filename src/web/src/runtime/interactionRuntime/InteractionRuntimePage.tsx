/**
 * Interaction Runtime Center — Sprint 29.6 foundation UI (not final design).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { interactionRuntime } from "@/runtime/interactionRuntime";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "session" | "selection" | "search" | "actions" | "history" | "events";

export function InteractionRuntimePage() {
  const [tab, setTab] = useState<Tab>("session");
  const [query, setQuery] = useState("hub");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return interactionRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Interaction Runtime · ADOS";
    rememberModuleRoute("/interactions");
    interactionRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 3000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "session", label: "Session" },
    { id: "selection", label: "Selection" },
    { id: "search", label: "Search" },
    { id: "actions", label: "Actions" },
    { id: "history", label: "History" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Interaction Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · catalog {snap.stats.catalog} · selection {snap.stats.selection} ·
            mode {snap.stats.selectionMode}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              interactionRuntime.select("building", "hub");
              refresh();
            }}
          >
            Select Hub
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              interactionRuntime.execute("create_meeting");
              refresh();
            }}
          >
            Create Meeting
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              interactionRuntime.open("citizen", "cit_owner_demo");
              refresh();
            }}
          >
            Open Owner
          </Button>
          <Link to="/city-visualization" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Viz →
          </Link>
          <Link to="/intelligence" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Intel →
          </Link>
          <Link to="/enterprise-city" className="eds-type-helper text-[var(--eds-primary)] self-center">
            City →
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

      {tab === "session" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Active Session">
            <ul className="eds-type-small space-y-1">
              <li>Id: {snap.session?.id || "—"}</li>
              <li>Surface: {snap.session?.surface}</li>
              <li>Actor: {snap.context?.actorCitizenId}</li>
              <li>Path: {snap.context?.path}</li>
              <li>Focus: {snap.context?.focus?.label || "—"}</li>
            </ul>
          </Card>
          <Card title="Stats">
            <ul className="eds-type-small space-y-1">
              <li>Sessions: {snap.stats.sessions}</li>
              <li>Actions: {snap.stats.actions}</li>
              <li>History: {snap.stats.history}</li>
              <li>Cache rev: {snap.stats.cache.revision}</li>
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "selection" ? (
        <Card title={`Selection (${snap.selection.mode})`}>
          <div className="flex flex-wrap gap-2 mb-3">
            <Button size="sm" variant="ghost" onClick={() => { interactionRuntime.setSelectionMode("multi"); refresh(); }}>
              Multi
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                interactionRuntime.selectHierarchy("district", "enterprise");
                refresh();
              }}
            >
              Hierarchy Enterprise
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                interactionRuntime.selectArea({ minX: 40, minY: 30, maxX: 60, maxY: 50 });
                refresh();
              }}
            >
              Area Center
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { interactionRuntime.clearSelection(); refresh(); }}>
              Clear
            </Button>
          </div>
          <ul className="eds-type-small space-y-1">
            {snap.selection.targets.map((t) => (
              <li key={`${t.kind}:${t.id}`}>
                <Badge>{t.kind}</Badge> {t.label}
              </li>
            ))}
            {!snap.selection.targets.length ? <li className="eds-type-helper">Nothing selected</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "search" ? (
        <Card title="Search & Nearby">
          <div className="mb-3 flex gap-2">
            <input
              className="eds-input flex-1"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search city objects"
            />
            <Button size="sm" onClick={refresh}>
              Search
            </Button>
          </div>
          <ul className="eds-type-small space-y-1 mb-4">
            {interactionRuntime.search(query, 8).map((h) => (
              <li key={`${h.target.kind}:${h.target.id}`}>
                [{h.score}] {h.target.kind} · {h.target.label}
              </li>
            ))}
          </ul>
          <p className="eds-type-helper mb-1">Nearby hub</p>
          <ul className="eds-type-small space-y-1">
            {snap.nearbySample.map((h) => (
              <li key={`n-${h.target.kind}:${h.target.id}`}>
                {h.target.kind} · {h.target.label}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "actions" ? (
        <Card title="Context Actions">
          <ul className="eds-type-small space-y-2">
            {snap.actions.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2">
                <span>{a.label}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    interactionRuntime.execute(a.id);
                    refresh();
                  }}
                >
                  Run
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "history" ? (
        <Card title="Interaction History">
          <ul className="eds-type-small space-y-1">
            {snap.history.map((h) => (
              <li key={h.id}>
                {h.at.slice(11, 19)} · {h.event}
                {h.actionId ? ` · ${h.actionId}` : ""}
                {h.result ? ` · ${h.result}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "events" ? (
        <Card title="Live Events">
          <ul className="eds-type-small space-y-1">
            {snap.events.map((e) => (
              <li key={e.id}>
                {e.at.slice(11, 19)} · {e.name}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
