/**
 * Mission Control strip for Command Center — Sprint 32.3.2 + live refresh 32.3.4.
 * Probes existing MC + OBS APIs; does not fork Mission Control engine.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { apiFetch } from "@/integrations/apiClient";
import { hubIntegrations } from "@/integrations/hub";
import { liveUpdates } from "../../workspace/realtime/liveUpdates";
import { PLATFORM_BUILDER_API } from "../../platform-builder/types";
import { RuntimeMonitorCompact } from "@/ai-runtime";
import { EnterpriseRuntimeMonitor } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { DataFabricOverviewCompact } from "@/enterprise-data-fabric";
import { PredictiveWidgetCompact } from "@/predictive-intelligence";
import { AutonomousWidgetCompact } from "@/autonomous-enterprise";
import { LearningWidgetCompact } from "@/self-learning-enterprise";
import { EnterpriseGoalsWidgetCompact } from "@/enterprise-okr";
import { GovernanceWidgetCompact } from "@/enterprise-governance";

type Dict = Record<string, unknown>;

export function MissionControlStrip() {
  const [mc, setMc] = useState<Dict | null>(null);
  const [obs, setObs] = useState<Dict | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [mcRes, obsRes] = await Promise.all([
        apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
      ]);
      setMc(mcRes.ok ? ((await mcRes.json()) as Dict) : null);
      setObs(obsRes.ok ? ((await obsRes.json()) as Dict) : null);
      if (!mcRes.ok && !obsRes.ok) setError("Mission Control / OBS temporarily unavailable");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Probe failed");
      // Keep last good MC/OBS payloads on transient failure
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    let last = 0;
    const unsub = liveUpdates.subscribe(() => {
      if (typeof document !== "undefined" && document.hidden) return;
      const now = Date.now();
      if (now - last < 12_000) return;
      last = now;
      void refresh();
    });
    return () => {
      unsub();
    };
  }, [refresh]);

  const obsReady =
    obs?.enterprise_observability_ready === true || obs?.status === "ok";

  return (
    <Card title="Mission Control">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone={mc ? "success" : "warning"}>{mc ? "Workspace linked" : "Partial"}</Badge>
        <Badge tone={obsReady ? "success" : "warning"}>
          AI / OBS {obsReady ? "active" : "check"}
        </Badge>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void refresh()}>
          Refresh
        </Button>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Open live Mission Control
          </Button>
        </Link>
        <Link to="/platform-builder/concierge">
          <Button size="sm">Ask Advisor next</Button>
        </Link>
      </div>
      {error ? <p className="mb-3 eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
      <div className="mb-4">
        <EnterpriseRuntimeMonitor />
        <RuntimeMonitorCompact />
        <DataFabricOverviewCompact />
        <PredictiveWidgetCompact />
        <AutonomousWidgetCompact />
        <LearningWidgetCompact />
        <EnterpriseGoalsWidgetCompact />
        <GovernanceWidgetCompact />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="cc-stat">
          <p className="cc-stat-label">Workspace</p>
          <p className="cc-stat-value">{mc ? "Operational" : "…"}</p>
        </div>
        <div className="cc-stat">
          <p className="cc-stat-label">System activity</p>
          <p className="cc-stat-value">{obsReady ? "Live" : "Idle"}</p>
        </div>
        <div className="cc-stat">
          <p className="cc-stat-label">AI status</p>
          <p className="cc-stat-value">Platform AI layers</p>
        </div>
        <div className="cc-stat">
          <p className="cc-stat-label">Recommendation</p>
          <p className="cc-stat-value eds-type-small">
            Проверьте экосистемы в{" "}
            <Link className="underline" to="/platform-builder/mission-control">
              MC Live
            </Link>
          </p>
        </div>
      </div>
      <p className="mt-4 eds-type-small text-[var(--eds-text-muted)]">
        Последние события и полная телеметрия — в существующем Mission Control Studio. Этот блок —
        командный обзор без дублирования движка.
      </p>
    </Card>
  );
}
