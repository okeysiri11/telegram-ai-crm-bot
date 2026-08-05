/**
 * Sprint 30.8 — Marketplace hub over existing Solution Hub + installState.
 * No second marketplace engine.
 */

import { useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { MARKETPLACE_SOLUTIONS } from "@/enterprise-marketplace/solutionCatalog";
import {
  installSolution,
  listInstalled,
  resolveStatus,
  setInstallStatus,
} from "@/enterprise-marketplace/installState";

const TABS = [
  { id: "installed", label: "Установленные" },
  { id: "available", label: "Доступные" },
  { id: "updates", label: "Обновления" },
  { id: "details", label: "Детали" },
] as const;

export function MarketplaceModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "available";
  const [selectedId, setSelectedId] = useState(MARKETPLACE_SOLUTIONS[0]?.id || "");
  const [tick, setTick] = useState(0);
  const active = TABS.some((t) => t.id === view) ? view : "available";

  const installed = useMemo(() => {
    void tick;
    return listInstalled();
  }, [tick]);

  const selected = MARKETPLACE_SOLUTIONS.find((s) => s.id === selectedId) || MARKETPLACE_SOLUTIONS[0];

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const available = MARKETPLACE_SOLUTIONS.filter((s) => {
    const st = resolveStatus(s);
    return st === "available" || st === "draft";
  });
  const installedSolutions = MARKETPLACE_SOLUTIONS.filter((s) => {
    const st = resolveStatus(s);
    return st === "installed" || st === "update";
  });
  const updates = MARKETPLACE_SOLUTIONS.filter((s) => resolveStatus(s) === "update");

  return (
    <BusinessModuleShell
      title="Маркетплейс"
      subtitle="Модули · установка · обновления"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source="Solution Hub"
      testId="marketplace-module"
      actions={
        <Link to="/platform-builder/solution-hub">
          <Button size="sm" variant="secondary">
            Solution Hub
          </Button>
        </Link>
      }
    >
      {active === "installed" ? (
        <div className="eds-grid eds-grid--dashboard">
          {installedSolutions.map((s) => (
            <Card key={s.id} title={s.title} status={<Badge tone="success">{resolveStatus(s)}</Badge>}>
              <p className="eds-type-helper">{s.description}</p>
              <Button
                size="sm"
                className="mt-2"
                onClick={() => {
                  setSelectedId(s.id);
                  setTab("details");
                }}
              >
                Детали
              </Button>
            </Card>
          ))}
          {!installedSolutions.length ? <p className="eds-type-helper">Нет установленных модулей</p> : null}
        </div>
      ) : null}

      {active === "available" ? (
        <div className="eds-grid eds-grid--dashboard">
          {available.map((s) => (
            <Card key={s.id} title={s.title} status={<Badge>{resolveStatus(s)}</Badge>}>
              <p className="eds-type-helper">{s.description}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    installSolution(s);
                    setTick((x) => x + 1);
                  }}
                >
                  Установить
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setSelectedId(s.id);
                    setTab("details");
                  }}
                >
                  Детали
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      {active === "updates" ? (
        <div className="eds-grid eds-grid--dashboard">
          {updates.map((s) => (
            <Card key={s.id} title={s.title}>
              <Button
                size="sm"
                onClick={() => {
                  setInstallStatus(s.id, "installed");
                  setTick((x) => x + 1);
                }}
              >
                Обновить до {s.version}
              </Button>
            </Card>
          ))}
          {!updates.length ? (
            <p className="eds-type-helper">
              Обновлений нет · установлено: {installed.length}
            </p>
          ) : null}
        </div>
      ) : null}

      {active === "details" && selected ? (
        <Card title={selected.title} status={<Badge>{selected.version}</Badge>}>
          <p className="eds-type-body">{selected.description}</p>
          <ul className="mt-3 space-y-1 eds-type-small">
            <li>AI Team: {selected.aiTeam.join(", ") || "—"}</li>
            <li>Workflows: {selected.workflows.join(", ") || "—"}</li>
            <li>Skills: {selected.skills.join(", ") || "—"}</li>
            <li>Prompts: {selected.prompts.join(", ") || "—"}</li>
          </ul>
          <Button
            className="mt-3"
            size="sm"
            onClick={() => {
              installSolution(selected);
              setTick((x) => x + 1);
            }}
          >
            Установить
          </Button>
        </Card>
      ) : null}
    </BusinessModuleShell>
  );
}
