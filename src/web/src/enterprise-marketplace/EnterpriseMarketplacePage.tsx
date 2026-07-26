/**
 * Enterprise Marketplace & Solution Hub — Sprint 32.9.
 * One-click install over Builder Studio catalogs — no new Marketplace Engine.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { webConfig } from "@/config/webConfig";
import { telemetry } from "@/integrations/telemetry";
import {
  MARKETPLACE_CATEGORIES,
  MARKETPLACE_SOLUTIONS,
  solutionsByCategory,
  type MarketplaceCategory,
  type MarketplaceSolution,
  type SolutionInstallStatus,
} from "./solutionCatalog";
import {
  checkCompatibility,
  installSolution,
  listInstalled,
  resolveStatus,
  setInstallStatus,
} from "./installState";

const STATUS_TONE: Record<SolutionInstallStatus, "default" | "success" | "warning" | "danger"> = {
  available: "default",
  installed: "success",
  update: "warning",
  disabled: "danger",
  draft: "warning",
};

export function EnterpriseMarketplacePage() {
  const [category, setCategory] = useState<MarketplaceCategory | "all" | "installed">("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const ecosystem = useMemo(() => {
    const blob = `${window.location.pathname} ${first.industry}`.toLowerCase();
    for (const id of ["beauty", "legal", "cafe", "auto", "agro", "drone", "crypto"]) {
      if (blob.includes(id) || (id === "crypto" && blob.includes("bidex"))) return id;
    }
    return "platform";
  }, [first.industry]);

  const solutions = useMemo(() => {
    void tick;
    if (category === "installed") {
      const ids = new Set(listInstalled().map((r) => r.solutionId));
      return MARKETPLACE_SOLUTIONS.filter((s) => ids.has(s.id) || resolveStatus(s) !== "available");
    }
    return solutionsByCategory(category === "all" ? "all" : category);
  }, [category, tick]);

  const selected = MARKETPLACE_SOLUTIONS.find((s) => s.id === selectedId) || null;

  const installedSummary = useMemo(() => {
    void tick;
    const all = MARKETPLACE_SOLUTIONS.map((s) => ({ s, status: resolveStatus(s) }));
    return {
      installed: all.filter((x) => x.status === "installed").length,
      update: all.filter((x) => x.status === "update").length,
      disabled: all.filter((x) => x.status === "disabled").length,
      draft: all.filter((x) => x.status === "draft").length,
    };
  }, [tick]);

  function refresh() {
    setTick((t) => t + 1);
  }

  function onInstall(sol: MarketplaceSolution) {
    const report = checkCompatibility(sol, {
      workspaceId: first.workspaceId || ws.project,
      ecosystem: String(ecosystem),
      roleId: first.roleId || user?.roleId,
      hasAccess: true,
      platformVersion: webConfig.version,
    });
    if (!report.ok) {
      setMessage("Установка заблокирована — проверьте Compatibility");
      setSelectedId(sol.id);
      return;
    }
    const rec = installSolution(sol);
    setMessage(
      `Установлено: Team=${rec.imported.team} · Skills=${rec.imported.skills} · Workflow=${rec.imported.workflows} · Prompts=${rec.imported.prompts}`,
    );
    void telemetry.userActivity(`mkt_install:${sol.id}`);
    refresh();
    setSelectedId(sol.id);
  }

  return (
    <WorkspaceLayout>
      <div className="mkt-hub eds-anim-fade">
        <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
              Enterprise Marketplace & Solution Hub
            </p>
            <h1 className="text-2xl font-semibold tracking-tight">Marketplace</h1>
            <p className="mt-1 max-w-2xl eds-type-small text-[var(--eds-text-muted)]">
              Подключайте готовые AI Teams, Workflows, Skills и Enterprise Packs без разработчика — поверх
              Builder Studio.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/platform-builder/builder-studio">
              <Button size="sm" variant="secondary">
                Builder Studio
              </Button>
            </Link>
            <Link to="/platform-builder/workflow-center">
              <Button size="sm" variant="ghost">
                Workflows
              </Button>
            </Link>
          </div>
        </header>

        <Card title="Installed Solutions" className="mb-3 mkt-installed">
          <ul className="flex flex-wrap gap-2 eds-type-small">
            <li>
              <Badge tone="success">Установлено {installedSummary.installed}</Badge>
            </li>
            <li>
              <Badge tone="warning">Обновления {installedSummary.update}</Badge>
            </li>
            <li>
              <Badge tone="danger">Отключено {installedSummary.disabled}</Badge>
            </li>
            <li>
              <Badge>Черновики {installedSummary.draft}</Badge>
            </li>
          </ul>
        </Card>

        {message ? <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">{message}</p> : null}

        <nav className="mkt-cats" aria-label="Marketplace categories">
          <button
            type="button"
            className={`mkt-cat${category === "all" ? " is-active" : ""}`}
            onClick={() => setCategory("all")}
          >
            All
          </button>
          <button
            type="button"
            className={`mkt-cat${category === "installed" ? " is-active" : ""}`}
            onClick={() => setCategory("installed")}
          >
            Installed
          </button>
          {MARKETPLACE_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`mkt-cat${category === c.id ? " is-active" : ""}`}
              onClick={() => setCategory(c.id)}
            >
              {c.label}
            </button>
          ))}
        </nav>

        <div className="mkt-grid mt-3">
          {solutions.map((sol) => {
            const status = resolveStatus(sol);
            return (
              <button
                key={sol.id}
                type="button"
                className={`mkt-card${selectedId === sol.id ? " is-active" : ""}`}
                onClick={() => setSelectedId(sol.id)}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <span className="font-semibold">{sol.title}</span>
                  <Badge tone={STATUS_TONE[status]}>{status}</Badge>
                </div>
                <p className="mt-1 eds-type-small text-[var(--eds-text-muted)]">{sol.description}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  <Badge>★ {sol.rating}</Badge>
                  <Badge>v{sol.version}</Badge>
                  {sol.enterprisePack ? <Badge tone="success">Enterprise</Badge> : null}
                </div>
                <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
                  Eco: {sol.ecosystems.join(", ")}
                </p>
              </button>
            );
          })}
        </div>

        {selected ? (
          <SolutionDetail
            solution={selected}
            ecosystem={String(ecosystem)}
            workspaceId={first.workspaceId || ws.project}
            roleId={first.roleId || user?.roleId || "owner"}
            onInstall={() => onInstall(selected)}
            onDisable={() => {
              setInstallStatus(selected.id, "disabled");
              refresh();
            }}
            onEnable={() => {
              setInstallStatus(selected.id, "installed");
              refresh();
            }}
          />
        ) : null}

        {category === "enterprise_hub" || category === "all" ? (
          <Card title="Enterprise Hub · корпоративные решения" className="mt-4">
            <p className="eds-type-small text-[var(--eds-text-muted)] mb-3">
              Семь Enterprise Packs для Business Ecosystems.
            </p>
            <div className="mkt-grid">
              {MARKETPLACE_SOLUTIONS.filter((s) => s.enterprisePack).map((sol) => (
                <button key={sol.id} type="button" className="mkt-card" onClick={() => setSelectedId(sol.id)}>
                  <span className="font-semibold">{sol.title}</span>
                  <span className="block eds-type-small text-[var(--eds-text-muted)]">{sol.description}</span>
                </button>
              ))}
            </div>
          </Card>
        ) : null}
      </div>
    </WorkspaceLayout>
  );
}

export function MarketplaceStrip() {
  const n = MARKETPLACE_SOLUTIONS.length;
  const packs = MARKETPLACE_SOLUTIONS.filter((s) => s.enterprisePack).length;
  return (
    <div className="mkt-strip" aria-label="Marketplace">
      <span className="mkt-strip-label">Marketplace</span>
      <Badge>{n} solutions</Badge>
      <Badge tone="success">{packs} packs</Badge>
      <Link
        to="/platform-builder/solution-hub"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("mkt_open")}
      >
        Hub →
      </Link>
    </div>
  );
}

function SolutionDetail({
  solution,
  ecosystem,
  workspaceId,
  roleId,
  onInstall,
  onDisable,
  onEnable,
}: {
  solution: MarketplaceSolution;
  ecosystem: string;
  workspaceId?: string;
  roleId?: string;
  onInstall: () => void;
  onDisable: () => void;
  onEnable: () => void;
}) {
  const status = resolveStatus(solution);
  const report = checkCompatibility(solution, {
    workspaceId,
    ecosystem,
    roleId,
    hasAccess: true,
    platformVersion: webConfig.version,
  });

  return (
    <div className="mkt-detail mt-4 space-y-3">
      <Card title={`Solution · ${solution.title}`}>
        <p className="eds-type-small text-[var(--eds-text-muted)]">{solution.description}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>★ {solution.rating}</Badge>
          <Badge>v{solution.version}</Badge>
          <Badge tone={STATUS_TONE[status]}>{status}</Badge>
        </div>
        <p className="mt-2 eds-type-small">
          Экосистемы: <strong>{solution.ecosystems.join(", ")}</strong>
        </p>
        <p className="eds-type-small">
          Роли: <strong>{solution.roles.join(", ")}</strong>
        </p>
      </Card>

      <div className="mkt-split">
        <Card title="Solution Preview">
          <PreviewBlock label="AI Team" items={solution.aiTeam} />
          <PreviewBlock label="Workflow" items={solution.workflows} />
          <PreviewBlock label="Skills" items={solution.skills} />
          <PreviewBlock label="Prompt Packs" items={solution.prompts} />
          <PreviewBlock label="Templates" items={solution.templates} />
        </Card>
        <Card title="Compatibility">
          <ul className="space-y-2 eds-type-small">
            {report.checks.map((c) => (
              <li key={c.id} className="flex flex-wrap items-center gap-2">
                <Badge tone={c.pass ? "success" : "danger"}>{c.pass ? "OK" : "Fail"}</Badge>
                <span className="font-medium">{c.label}</span>
                <span className="text-[var(--eds-text-muted)]">{c.detail}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap gap-2">
            {status === "available" || status === "draft" || status === "update" ? (
              <Button disabled={!report.ok} onClick={onInstall}>
                One-Click Install
              </Button>
            ) : null}
            {status === "installed" || status === "update" ? (
              <Button size="sm" variant="ghost" onClick={onDisable}>
                Отключить
              </Button>
            ) : null}
            {status === "disabled" ? (
              <Button size="sm" variant="secondary" onClick={onEnable}>
                Включить
              </Button>
            ) : null}
            <Link to="/platform-builder/builder-studio">
              <Button size="sm" variant="ghost">
                Open Builder
              </Button>
            </Link>
            {solution.workflows[0] ? (
              <Link to={`/platform-builder/workflow-center?wf=${solution.workflows[0]}`}>
                <Button size="sm" variant="ghost">
                  Open Workflow
                </Button>
              </Link>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

function PreviewBlock({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="mb-2">
      <p className="font-medium eds-type-small">{label}</p>
      {items.length ? (
        <div className="mt-1 flex flex-wrap gap-1">
          {items.map((i) => (
            <Badge key={i}>{i}</Badge>
          ))}
        </div>
      ) : (
        <p className="eds-type-small text-[var(--eds-text-muted)]">· —</p>
      )}
    </div>
  );
}
