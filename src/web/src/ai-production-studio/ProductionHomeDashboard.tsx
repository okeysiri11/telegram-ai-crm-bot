/**
 * Sprint 32.0 — Production Home dashboard (nav + content types + owner pulse).
 */

import { Badge, Button, Card } from "@/ui";
import { useProductionStore } from "./productionStore";
import { CONTENT_TYPES, PRODUCTION_HOME_NAV } from "./contentTypes";
import { deriveProductionOwnerStats } from "./productionAnalytics";
import { PRODUCTION_STUDIOS } from "./productionCatalog";
import { useMemo } from "react";

export function ProductionHomeDashboard() {
  const setView = useProductionStore((s) => s.setView);
  const openStudio = useProductionStore((s) => s.openStudio);
  const generateInStudio = useProductionStore((s) => s.generateInStudio);
  const generations = useProductionStore((s) => s.generations);
  const prompts = useProductionStore((s) => s.prompts);
  const jobs = useProductionStore((s) => s.jobs);
  const pipelines = useProductionStore((s) => s.pipelines);
  const brandKit = useProductionStore((s) => s.brandKit);

  const stats = useMemo(
    () => deriveProductionOwnerStats({ generations, prompts, jobs, pipelines }),
    [generations, prompts, jobs, pipelines],
  );
  const brand = brandKit();

  return (
    <div className="space-y-4 edm-page-soft" data-testid="production-home">
      <Card title="Production Home" status={<Badge tone="success">MVP 32.0</Badge>}>
        <p className="eds-type-helper mb-3">
          Бренд {brand.name} · Runtime = SoR · APH providers · n8n только оркестрация
        </p>
        <div className="flex flex-wrap gap-2">
          {PRODUCTION_HOME_NAV.map((item) => (
            <Button
              key={item.id}
              size="sm"
              variant="secondary"
              toolbar
              onClick={() => setView(item.view)}
            >
              {item.labelRu}
            </Button>
          ))}
        </div>
      </Card>

      <div className="eds-grid eds-grid--dashboard">
        <Card title="Генерации">
          <p className="font-semibold">{stats.totalGenerations}</p>
          <p className="eds-type-helper">
            done {stats.completed} · run {stats.running} · fail {stats.failed}
          </p>
        </Card>
        <Card title="Очереди">
          <p className="eds-type-small">
            gen {stats.queueStatus.generation} · render {stats.queueStatus.render} · task{" "}
            {stats.queueStatus.task}
          </p>
        </Card>
        <Card title="Стоимость">
          <p className="font-semibold">${stats.costTotalUsd}</p>
          <p className="eds-type-helper">{stats.tokensTotal} tok</p>
        </Card>
        <Card title="Топ шаблоны">
          <ul className="eds-type-small space-y-1">
            {stats.topTemplates.slice(0, 3).map((t) => (
              <li key={t.id}>
                {t.title} · {t.uses}
              </li>
            ))}
            {!stats.topTemplates.length ? <li className="eds-type-helper">Пока пусто</li> : null}
          </ul>
        </Card>
      </div>

      <Card title="Типы контента">
        <div className="flex flex-wrap gap-2">
          {CONTENT_TYPES.map((c) => (
            <Button
              key={c.id}
              size="sm"
              variant="ghost"
              toolbar
              onClick={() => {
                openStudio(c.studioId);
                generateInStudio(c.studioId, { multiAgent: true, title: `${c.labelRu} · run` });
              }}
            >
              {c.labelRu}
            </Button>
          ))}
        </div>
      </Card>

      <Card title="Студии">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {PRODUCTION_STUDIOS.filter((s) => s.group === "generate" || s.group === "brand").map((s) => (
            <button
              key={s.id}
              type="button"
              className="rounded-md border border-[var(--ew-border)] px-3 py-2 text-left hover:border-[var(--eds-primary)]"
              onClick={() => openStudio(s.id)}
            >
              <p className="font-medium eds-type-small">{s.labelRu || s.label}</p>
              <p className="eds-type-helper">{s.description}</p>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}
