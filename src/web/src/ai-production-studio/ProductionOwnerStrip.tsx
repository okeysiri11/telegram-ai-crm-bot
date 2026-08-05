/**
 * Sprint 32.0 — Owner production analytics strip.
 */

import { Link } from "react-router-dom";
import { useEffect, useMemo } from "react";
import { Badge, Card } from "@/ui";
import { useProductionStore } from "./productionStore";
import { deriveProductionOwnerStats } from "./productionAnalytics";

export function ProductionOwnerStrip() {
  const generations = useProductionStore((s) => s.generations);
  const prompts = useProductionStore((s) => s.prompts);
  const jobs = useProductionStore((s) => s.jobs);
  const pipelines = useProductionStore((s) => s.pipelines);
  const hydrate = useProductionStore((s) => s.hydrate);
  const hydrated = useProductionStore((s) => s.hydrated);

  useEffect(() => {
    if (!hydrated) hydrate();
  }, [hydrated, hydrate]);

  const stats = useMemo(
    () => deriveProductionOwnerStats({ generations, prompts, jobs, pipelines }),
    [generations, prompts, jobs, pipelines],
  );

  return (
    <Card
      title="Production Analytics"
      status={<Badge tone="success">Owner</Badge>}
      data-testid="production-owner-strip"
    >
      <div className="eds-grid eds-grid--dashboard">
        <div>
          <p className="eds-type-caption">Всего генераций</p>
          <p className="font-semibold">{stats.totalGenerations}</p>
        </div>
        <div>
          <p className="eds-type-caption">Провайдеры</p>
          <p className="eds-type-small">
            {stats.providerUsage
              .filter((p) => p.jobs)
              .map((p) => `${p.title}:${p.jobs}`)
              .join(" · ") || "—"}
          </p>
        </div>
        <div>
          <p className="eds-type-caption">Очередь</p>
          <p className="eds-type-small">
            gen {stats.queueStatus.generation} · render {stats.queueStatus.render}
          </p>
        </div>
        <div>
          <p className="eds-type-caption">Cost</p>
          <p className="font-semibold">${stats.costTotalUsd}</p>
        </div>
        <div>
          <p className="eds-type-caption">Top templates</p>
          <p className="eds-type-small">
            {stats.topTemplates.map((t) => t.title).slice(0, 2).join(" · ") || "—"}
          </p>
        </div>
        <div>
          <p className="eds-type-caption">Top agents</p>
          <p className="eds-type-small">
            {stats.topAgents.map((a) => a.name).slice(0, 2).join(" · ") || "—"}
          </p>
        </div>
      </div>
      <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/production-studio">
        Открыть Production Studio →
      </Link>
    </Card>
  );
}
