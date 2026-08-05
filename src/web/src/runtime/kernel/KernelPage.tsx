/**
 * Kernel dashboard — Sprint 29.9 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { enterpriseKernel } from "@/runtime/kernel";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "state" | "boot" | "modules" | "diagnostics" | "recovery" | "config";

export function KernelPage() {
  const [tab, setTab] = useState<Tab>("state");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return enterpriseKernel.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Enterprise Kernel · ADOS";
    rememberModuleRoute("/kernel");
    enterpriseKernel.boot();
    const id = window.setInterval(() => setTick((n) => n + 1), 4000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    enterpriseKernel.healthSnapshot();
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "state", label: "Platform State" },
    { id: "boot", label: "Boot Sequence" },
    { id: "modules", label: "Modules" },
    { id: "diagnostics", label: "Diagnostics" },
    { id: "recovery", label: "Recovery" },
    { id: "config", label: "Configuration" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Kernel</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · phase {snap.status.phase} ·{" "}
            {snap.status.ready ? "ready" : "not ready"}
            {snap.status.degraded ? " · degraded" : ""} · boot{" "}
            {snap.status.startupTimeMs ?? "—"}ms
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
              enterpriseKernel.diagnostics();
              refresh();
            }}
          >
            Diagnostics
          </Button>
          <Link to="/orchestrator" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Orch →
          </Link>
          <Link to="/intelligence" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Intel →
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

      {tab === "state" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Platform State">
            <ul className="eds-type-small space-y-1">
              <li>
                Phase: <Badge>{snap.status.phase}</Badge>
              </li>
              <li>Ready: {String(snap.status.ready)}</li>
              <li>Degraded: {String(snap.status.degraded)}</li>
              <li>
                Health: {snap.status.health.runtimeHealthy}/{snap.status.health.runtimeTotal} ·
                platform {snap.status.health.platformStatus}
              </li>
              <li>EventBus: {snap.status.health.eventBusOk ? "ok" : "error"}</li>
              <li>Version: {snap.status.identity.kernel}</li>
            </ul>
          </Card>
          <Card title="Memory / Timing">
            <ul className="eds-type-small space-y-1">
              <li>Startup: {snap.diagnostics.startupTimeMs ?? "—"} ms</li>
              <li>
                JS heap:{" "}
                {snap.diagnostics.memory.available
                  ? `${snap.diagnostics.memory.usedJsHeapMb} / ${snap.diagnostics.memory.totalJsHeapMb} MB`
                  : "n/a"}
              </li>
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "boot" ? (
        <Card title="Boot Sequence">
          <ol className="eds-type-small space-y-2">
            {snap.bootSequence.map((s) => (
              <li key={s.id} className="flex flex-wrap gap-2 items-center">
                <Badge>{s.status}</Badge>
                <span>{s.label}</span>
                {s.durationMs != null ? (
                  <span className="eds-type-helper">{s.durationMs}ms</span>
                ) : null}
                {s.error ? <span className="eds-type-helper">{s.error}</span> : null}
              </li>
            ))}
          </ol>
        </Card>
      ) : null}

      {tab === "modules" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.modules.map((m) => (
            <Card key={m.id} title={m.label}>
              <div className="flex flex-wrap gap-2 mb-1">
                <Badge>{m.kind}</Badge>
                <Badge>{m.status}</Badge>
                <Badge>v{m.version}</Badge>
              </div>
              <p className="eds-type-helper">{m.loaded ? "loaded" : "not loaded"}</p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "diagnostics" ? (
        <Card title="Diagnostics">
          <ul className="eds-type-small space-y-1">
            <li>Failed modules: {snap.diagnostics.failedModules.join(", ") || "—"}</li>
            <li>Dependency errors: {snap.diagnostics.dependencyErrors.join(", ") || "—"}</li>
            <li>Version mismatches: {snap.diagnostics.versionMismatches.join(", ") || "—"}</li>
            <li>
              Config problems: {snap.diagnostics.configurationProblems.join(", ") || "—"}
            </li>
            <li>Notes: {snap.diagnostics.notes.join(", ") || "—"}</li>
          </ul>
        </Card>
      ) : null}

      {tab === "recovery" ? (
        <Card title="Recovery History">
          <ul className="eds-type-small space-y-1">
            {snap.recoveryHistory.map((r) => (
              <li key={r.id}>
                {r.at.slice(11, 19)} · {r.action} · {r.runtimeId || "platform"} ·{" "}
                <Badge>{r.ok ? "ok" : "fail"}</Badge> · {r.message}
              </li>
            ))}
            {!snap.recoveryHistory.length ? (
              <li className="eds-type-helper">No recovery events</li>
            ) : null}
          </ul>
          <Button
            size="sm"
            className="mt-3"
            variant="ghost"
            onClick={() => {
              enterpriseKernel.recover("intelligence");
              refresh();
            }}
          >
            Probe recover intelligence
          </Button>
        </Card>
      ) : null}

      {tab === "config" ? (
        <Card title="Configuration">
          <ul className="eds-type-small space-y-1">
            <li>Environment: {snap.status.config.environment}</li>
            <li>License: {snap.status.config.license.mode} · verified {String(snap.status.config.license.verified)}</li>
            <li>Orchestrator: {String(snap.status.config.featureFlags.orchestratorEnabled)}</li>
            <li>Recovery: {String(snap.status.config.featureFlags.recoveryEnabled)}</li>
            <li>Diagnostics: {String(snap.status.config.featureFlags.diagnosticsEnabled)}</li>
            <li>Boot timeout: {snap.status.config.bootTimeoutMs}ms</li>
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
