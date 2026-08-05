/**
 * Intelligence Runtime Center — Sprint 29.7 foundation UI (advisory only).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { intelligenceRuntime } from "@/runtime/intelligenceRuntime";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "analytics" | "insights" | "recommendations" | "risks" | "trends" | "events";

export function IntelligenceRuntimePage() {
  const [tab, setTab] = useState<Tab>("analytics");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return intelligenceRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Intelligence Runtime · ADOS";
    rememberModuleRoute("/intelligence");
    intelligenceRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 4000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    intelligenceRuntime.analyze({ force: true });
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "analytics", label: "Analytics" },
    { id: "insights", label: "Insights" },
    { id: "recommendations", label: "Recommendations" },
    { id: "risks", label: "Risks" },
    { id: "trends", label: "Trends" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Intelligence Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · advisory only · rev {snap.cycle.revision} ·{" "}
            {snap.stats.insights} insights · {snap.stats.recommendations} recommendations ·{" "}
            {snap.stats.risks} risks
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={refresh}>
            Analyze Now
          </Button>
          <Badge>No auto-execute</Badge>
          <Link to="/interactions" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Interact →
          </Link>
          <Link to="/dashboard" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Command →
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

      {tab === "analytics" ? (
        <Card title="Live Analytics">
          <ul className="eds-type-small space-y-1">
            <li>Business activity: {snap.cycle.analytics.businessActivity}</li>
            <li>Workflow bottlenecks: {snap.cycle.analytics.workflowBottlenecks}</li>
            <li>Citizens online: {snap.cycle.analytics.citizenOnline}</li>
            <li>Asset utilization: {snap.cycle.analytics.assetUtilizationPct}%</li>
            <li>Partner relations: {snap.cycle.analytics.partnerRelations}</li>
            <li>Project health: {snap.cycle.analytics.projectHealth}</li>
            <li>District activity avg: {snap.cycle.analytics.districtActivityAvg}</li>
            <li>Open risks: {snap.cycle.analytics.openRisks}</li>
          </ul>
          <p className="eds-type-helper mt-3">
            Policy: autonomousExecution={String(snap.policy.autonomousExecution)} ·
            requiresApproval={String(snap.policy.recommendationsRequireApproval)}
          </p>
        </Card>
      ) : null}

      {tab === "insights" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.cycle.insights.map((i) => (
            <Card key={i.id} title={i.title}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{i.category}</Badge>
                <Badge>{i.severity}</Badge>
              </div>
              <p className="eds-type-helper">{i.summary}</p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "recommendations" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.cycle.recommendations.map((r) => (
            <Card key={r.id} title={r.title}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{r.audience}</Badge>
                <Badge>{r.priority}</Badge>
                <Badge>approval required</Badge>
              </div>
              <p className="eds-type-helper">{r.rationale}</p>
              {r.suggestedRoute ? (
                <p className="eds-type-small mt-1">Suggested route: {r.suggestedRoute}</p>
              ) : null}
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "risks" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.cycle.risks.map((r) => (
            <Card key={r.id} title={r.title}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{r.kind}</Badge>
                <Badge>{r.severity}</Badge>
              </div>
              <p className="eds-type-helper">{r.detail}</p>
              {r.mitigationHint ? (
                <p className="eds-type-small mt-1">{r.mitigationHint}</p>
              ) : null}
            </Card>
          ))}
          {!snap.cycle.risks.length ? (
            <Card title="Risks">
              <p className="eds-type-helper">No advisory risks in current cycle</p>
            </Card>
          ) : null}
        </div>
      ) : null}

      {tab === "trends" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.cycle.trends.map((t) => (
            <Card key={t.id} title={t.label}>
              <ul className="eds-type-small space-y-1">
                {t.points.map((p) => (
                  <li key={p.key}>
                    {p.label}: {p.value} ({p.direction}
                    {p.delta ? ` ${p.delta > 0 ? "+" : ""}${p.delta}` : ""})
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "events" ? (
        <Card title="Intelligence Events">
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
