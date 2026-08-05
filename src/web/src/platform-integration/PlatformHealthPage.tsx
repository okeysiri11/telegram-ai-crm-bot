/**
 * Sprint 30.6 — Platform Health dashboard.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card } from "@/ui";
import { healthService } from "@/enterprise-runtime/healthService";
import { EnterpriseRuntimeMonitor } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { derivePlatformHealth } from "./platformHealth";

export function PlatformHealthPage() {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    document.title = "Platform Health · ADOS";
    const unsub = healthService.subscribe(() => setTick((t) => t + 1));
    return unsub;
  }, []);

  const h = useMemo(() => {
    void tick;
    return derivePlatformHealth();
  }, [tick]);

  return (
    <WorkspaceLayout>
      <div className="stack-lg" style={{ maxWidth: 1100, margin: "0 auto" }} data-testid="platform-health">
        <header className="ews-glass" style={{ padding: "1rem 1.25rem", borderRadius: "var(--eds-radius-2xl)" }}>
          <div className="row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
                Platform Health · Sprint 30.6
              </p>
              <h1 className="text-2xl font-semibold tracking-tight">Здоровье платформы</h1>
              <p className="eds-type-helper mt-1">
                CPU · Memory · Workers · Runtime · API · Database · Cache
              </p>
            </div>
            <div className="row" style={{ gap: 8, alignItems: "center" }}>
              <Badge tone={h.level === "healthy" ? "success" : h.level === "critical" ? "danger" : "warning"}>
                {h.level}
              </Badge>
              <Link to="/owner">
                <Button size="sm" variant="secondary">
                  Owner
                </Button>
              </Link>
              <Link to="/platform-builder/mission-control">
                <Button size="sm" variant="ghost">
                  Mission Control
                </Button>
              </Link>
            </div>
          </div>
          <div className="mt-3">
            <EnterpriseRuntimeMonitor />
          </div>
        </header>

        <div className="eds-grid eds-grid--dashboard">
          <MetricCard label="CPU" value={`${h.cpuPct}%`} />
          <MetricCard label="Memory" value={`${h.memoryPct}%`} />
          <MetricCard label="Workers" value={`${h.workersBusy}/${h.workersTotal}`} />
          <MetricCard label="Runtime" value={h.runtimeStatus} />
          <MetricCard label="API" value={h.apiTone} />
          <MetricCard label="Database" value={h.databaseTone} />
          <MetricCard label="Cache" value={h.cacheTone} />
          <MetricCard label="Queue" value={String(h.queueLength)} />
          <MetricCard label="AI Agents" value={String(h.agentsActive)} />
        </div>

        <Card title="Пробы">
          <ul className="space-y-2">
            {h.items.map((item) => (
              <li key={item.id} className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                <span className="eds-type-small">
                  <strong>{item.label}</strong> · {item.detail}
                </span>
                <Badge
                  tone={
                    item.tone === "ok" ? "success" : item.tone === "err" ? "danger" : item.tone === "warn" ? "warning" : "default"
                  }
                >
                  {item.tone}
                </Badge>
              </li>
            ))}
          </ul>
          {h.updatedAt ? (
            <p className="eds-type-helper mt-3">Обновлено: {new Date(h.updatedAt).toLocaleString()}</p>
          ) : null}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card title={label}>
      <p className="text-2xl font-semibold">{value}</p>
    </Card>
  );
}
