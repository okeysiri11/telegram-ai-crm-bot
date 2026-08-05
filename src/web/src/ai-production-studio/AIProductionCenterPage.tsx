/**
 * AI Production Center — Sprint 27.9.
 * Professional creative studio shell on Enterprise Desktop / City.
 * Reuses WorkspaceLayout, design system, live status, Concierge — no second platform.
 */

import { lazy, Suspense, useEffect, useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useIntegrationRuntimeHealth, useSharedContext, enterpriseEventBus } from "@/integration-hub";
import { EnterpriseRuntimeMonitor } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { jobManager } from "@/enterprise-runtime/jobManager";
import { webConfig } from "@/config/webConfig";
import { ProductionProviderStrip } from "@/enterprise-integrations";
import { ProductionHomeDashboard } from "./ProductionHomeDashboard";
import { BrandKitPanel } from "./BrandKitPanel";
import { WorkflowBuilderPanel } from "./WorkflowBuilderPanel";
import { TaskQueuePanel } from "./TaskQueuePanel";
import {
  PIPELINE_STAGES,
  PRODUCTION_CENTER_VERSION,
  PRODUCTION_QUICK_ACTIONS_RU,
  studioById,
  type ProductionStudioId,
} from "./productionCatalog";
import { useProductionStore } from "./productionStore";

const StudioWorkspace = lazy(() =>
  import("./StudioWorkspace").then((m) => ({ default: m.StudioWorkspace })),
);
const ProductionRuntimePanel = lazy(() =>
  import("@/enterprise-runtime/ProductionRuntimePanel").then((m) => ({
    default: m.ProductionRuntimePanel,
  })),
);
const PromptStudioPanel = lazy(() =>
  import("./PromptStudioPanel").then((m) => ({ default: m.PromptStudioPanel })),
);
const LibraryBrowser = lazy(() =>
  import("./LibraryBrowser").then((m) => ({ default: m.LibraryBrowser })),
);
const ProjectExplorer = lazy(() =>
  import("./ProjectExplorer").then((m) => ({ default: m.ProjectExplorer })),
);
const GenerationHistoryPanel = lazy(() =>
  import("./GenerationHistoryPanel").then((m) => ({ default: m.GenerationHistoryPanel })),
);

export function AIProductionCenterPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const hydrate = useProductionStore((s) => s.hydrate);
  const hydrated = useProductionStore((s) => s.hydrated);
  const view = useProductionStore((s) => s.view);
  const setView = useProductionStore((s) => s.setView);
  const openStudio = useProductionStore((s) => s.openStudio);
  const activeStudioId = useProductionStore((s) => s.activeStudioId);
  const pipelines = useProductionStore((s) => s.pipelines);
  const jobs = useProductionStore((s) => s.jobs);
  const createPipeline = useProductionStore((s) => s.createPipeline);
  const runUniversalPipeline = useProductionStore((s) => s.runUniversalPipeline);
  const items = useNotificationStore((s) => s.items);
  const unread = useMemo(() => items.filter((i) => !i.read).length, [items]);
  const { items: health } = useIntegrationRuntimeHealth();
  const ctx = useSharedContext();
  const aiOk = health.find((h) => h.id === "ai")?.tone !== "err";

  useEffect(() => {
    hydrate();
    document.title = "AI Production Center · ADOS";
    runtimeEngine.publishStream("production", { surface: "production" });
  }, [hydrate]);

  useEffect(() => {
    if (jobs?.length) jobManager.syncProductionJobs(jobs);
  }, [jobs]);

  const studioParam = params.get("studio");
  const tabParam = params.get("tab");
  useEffect(() => {
    const studio = studioParam as ProductionStudioId | null;
    if (studio && studioById(studio)) {
      openStudio(studio);
      enterpriseEventBus.openProduction(studio);
    }
    const tab = tabParam;
    if (
      tab === "pipeline" ||
      tab === "prompts" ||
      tab === "media" ||
      tab === "automation" ||
      tab === "runtime" ||
      tab === "projects" ||
      tab === "history"
    ) {
      setView(tab);
      enterpriseEventBus.openProduction(undefined, tab);
    }
  }, [studioParam, tabParam, openStudio, setView]);

  const running = useMemo(() => jobs.filter((j) => j.status === "running" || j.status === "queued").length, [jobs]);

  if (!hydrated) {
    return (
      <WorkspaceLayout>
        <div className="p-6 space-y-3" data-testid="production-studio-skeleton">
          <div className="edm-skeleton h-8 w-72 rounded-md" />
          <div className="edm-skeleton h-28 w-full rounded-lg" />
          <p className="eds-type-helper">Загрузка Production Center…</p>
        </div>
      </WorkspaceLayout>
    );
  }

  return (
    <WorkspaceLayout>
      <div className="stack-lg edm-page" style={{ maxWidth: 1400, margin: "0 auto" }}>
        <header className="ews-glass" style={{ padding: "1rem 1.25rem", borderRadius: "var(--eds-radius-2xl)" }}>
          <div className="row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
                AI Production Studio · {PRODUCTION_CENTER_VERSION}
              </p>
              <h1 className="text-2xl font-semibold tracking-tight">Продакшн-студия</h1>
              <p className="eds-type-helper mt-1 max-w-2xl">
                Изображения · Видео · Reels · TikTok · Instagram · YouTube · Презентации · Голос · Промпты · Бренд
              </p>
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <Badge tone={aiOk ? "success" : "warning"}>AI {aiOk ? "live" : "проверка"}</Badge>
              <Badge tone={running ? "info" : "default"}>Задачи {running}</Badge>
              {unread ? <Badge tone="warning">Алерты {unread}</Badge> : null}
              <Badge>{ctx.organization}</Badge>
              <span className="eds-type-helper">{ctx.workspaceId}</span>
              <Link to="/ai-agents">
                <Button size="sm" variant="secondary">
                  AI-Агенты
                </Button>
              </Link>
              <Link to="/ai-studio">
                <Button size="sm" variant="secondary">
                  AI Studio
                </Button>
              </Link>
              <Link to="/enterprise-city">
                <Button size="sm" variant="secondary">
                  Город
                </Button>
              </Link>
              <Link to="/desktop">
                <Button size="sm" variant="ghost">
                  Desktop
                </Button>
              </Link>
              <span className="eds-type-helper">Sprint {webConfig.sprint}</span>
            </div>
          </div>
          <div className="mt-3">
            <EnterpriseRuntimeMonitor />
          </div>
          <div className="mt-3">
            <ProductionProviderStrip compact />
          </div>
          <nav className="row mt-3" style={{ gap: 6, flexWrap: "wrap" }} aria-label="Быстрые действия продакшна">
            {PRODUCTION_QUICK_ACTIONS_RU.map((a) => (
              <Button
                key={a.id}
                size="sm"
                variant="primary"
                toolbar
                onClick={() => {
                  openStudio(a.studioId);
                  const def = studioById(a.studioId);
                  if (def) {
                    createPipeline(a.label, a.studioId, def.aiAgents);
                    runUniversalPipeline(a.studioId);
                  }
                }}
              >
                {a.label}
              </Button>
            ))}
          </nav>
          <nav className="row mt-3" style={{ gap: 6, flexWrap: "wrap" }} aria-label="Разделы продакшна">
            {(
              [
                ["home", "Главная"],
                ["projects", "Проекты"],
                ["pipeline", "Конвейер"],
                ["queue", "Очереди"],
                ["runtime", "Runtime"],
                ["prompts", "Промпты"],
                ["brand", "Бренд"],
                ["templates", "Шаблоны"],
                ["assets", "Ассеты"],
                ["media", "Медиатека"],
                ["history", "История"],
                ["automation", "Агенты"],
              ] as const
            ).map(([id, label]) => (
              <Button
                key={id}
                size="sm"
                variant={view === id || (view === "studio" && id === "home") ? "primary" : "ghost"}
                toolbar
                onClick={() => setView(id === "home" ? "home" : id)}
              >
                {label}
              </Button>
            ))}
            <Button
              size="sm"
              variant="secondary"
              toolbar
              onClick={() => {
                const studio = activeStudioId || "creative";
                const def = studioById(studio)!;
                createPipeline(`New · ${def.short}`, studio, def.aiAgents);
              }}
            >
              Новый конвейер
            </Button>
            <Button
              size="sm"
              variant="secondary"
              toolbar
              onClick={() => {
                const studio = activeStudioId || "reels";
                runUniversalPipeline(studio);
              }}
            >
              Запуск Runtime
            </Button>
          </nav>
        </header>

        {view === "home" ? <ProductionHomeDashboard /> : null}
        {view === "studio" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading studio…</p>}>
            <StudioWorkspace />
          </Suspense>
        ) : null}

        {view === "pipeline" ? <WorkflowBuilderPanel /> : null}
        {view === "queue" ? <TaskQueuePanel /> : null}
        {view === "brand" ? <BrandKitPanel /> : null}
        {view === "projects" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading projects…</p>}>
            <ProjectExplorer />
          </Suspense>
        ) : null}
        {view === "runtime" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading Production Runtime…</p>}>
            <ProductionRuntimePanel />
          </Suspense>
        ) : null}
        {view === "prompts" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading prompts…</p>}>
            <PromptStudioPanel />
          </Suspense>
        ) : null}
        {view === "media" || view === "templates" || view === "assets" || view === "gallery" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading library…</p>}>
            <LibraryBrowser
              mode={view === "templates" ? "templates" : view === "assets" ? "assets" : "media"}
            />
          </Suspense>
        ) : null}
        {view === "history" || view === "favorites" ? (
          <Suspense fallback={<p className="eds-type-helper">Loading history…</p>}>
            <GenerationHistoryPanel />
          </Suspense>
        ) : null}
        {view === "automation" ? <AutomationPanel /> : null}

        <Card title="Platform links">
          <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/workflow-center")}>
              Workflow Center
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/runtime")}>
              AI Runtime
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/builder-studio")}>
              AI Builder (agents)
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/concierge")}>
              Concierge
            </Button>
            <Button size="sm" variant="ghost" onClick={() => navigate("/projects")}>
              Projects hub
            </Button>
          </div>
          <p className="eds-type-helper mt-2">
            Pipelines: {pipelines.length} · Approval rule: AI never publishes alone.
          </p>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function PipelinePanel() {
  const pipelines = useProductionStore((s) => s.pipelines);
  const advance = useProductionStore((s) => s.advancePipeline);
  const retreat = useProductionStore((s) => s.retreatPipeline);
  const setStage = useProductionStore((s) => s.setPipelineStage);
  const setAgents = useProductionStore((s) => s.setAgentChain);
  const prompts = useProductionStore((s) => s.prompts);
  const attachPrompt = useProductionStore((s) => s.attachPrompt);

  return (
    <div className="stack-md">
      <Card title="Pipeline Builder">
        <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
          {PIPELINE_STAGES.map((s) => (
            <Badge key={s.id}>{s.label}</Badge>
          ))}
        </div>
        <ul className="stack-md">
          {pipelines.map((p) => {
            const studio = studioById(p.studioId);
            return (
              <li key={p.id} className="ews-glass" style={{ padding: 12, borderRadius: "var(--eds-radius-xl)" }}>
                <div className="row" style={{ justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                  <div>
                    <p className="font-semibold">{p.title}</p>
                    <p className="eds-type-helper">
                      {studio?.label} · stage <Badge tone="info">{p.stage}</Badge>
                    </p>
                  </div>
                  <div className="row" style={{ gap: 6 }}>
                    <Button size="sm" variant="ghost" onClick={() => retreat(p.id)}>
                      ←
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => advance(p.id)}>
                      Advance →
                    </Button>
                  </div>
                </div>
                <div className="row mt-2" style={{ gap: 6, flexWrap: "wrap" }}>
                  {PIPELINE_STAGES.map((s) => (
                    <Button
                      key={s.id}
                      size="sm"
                      variant={p.stage === s.id ? "primary" : "ghost"}
                      toolbar
                      onClick={() => setStage(p.id, s.id)}
                    >
                      {s.label}
                    </Button>
                  ))}
                </div>
                <div className="mt-3">
                  <p className="eds-type-caption">AI agent chain</p>
                  <Input
                    value={p.agentChain.join(" → ")}
                    onChange={(e) =>
                      setAgents(
                        p.id,
                        e.target.value
                          .split("→")
                          .map((x) => x.trim())
                          .filter(Boolean),
                      )
                    }
                    aria-label="Agent chain"
                  />
                </div>
                <div className="mt-2">
                  <label className="eds-type-caption">Attach prompt</label>
                  <select
                    className="eds-input"
                    value={p.promptId || ""}
                    onChange={(e) => attachPrompt(p.id, e.target.value)}
                    style={{ display: "block", width: "100%", marginTop: 4 }}
                  >
                    <option value="">—</option>
                    {prompts.map((pr) => (
                      <option key={pr.id} value={pr.id}>
                        {pr.title}
                      </option>
                    ))}
                  </select>
                </div>
              </li>
            );
          })}
        </ul>
      </Card>
    </div>
  );
}

function AutomationPanel() {
  const jobs = useProductionStore((s) => s.jobs);
  const enqueue = useProductionStore((s) => s.enqueueJob);
  const retry = useProductionStore((s) => s.retryJob);

  return (
    <Card title="Automation Center">
      <div className="row" style={{ gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => enqueue({ title: "Batch export pack", kind: "batch", notify: true })}
        >
          Enqueue batch
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() =>
            enqueue({
              title: "Scheduled publish",
              kind: "schedule",
              notify: true,
              scheduleAt: new Date().toISOString(),
            })
          }
        >
          Schedule job
        </Button>
        <Link to="/automation">
          <Button size="sm" variant="ghost">
            Open Automation hub
          </Button>
        </Link>
      </div>
      <ul className="stack-sm">
        {jobs.map((j) => (
          <li key={j.id} className="row" style={{ justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
            <span>
              <strong>{j.title}</strong>
              <span className="eds-type-helper">
                {" "}
                · {j.kind} · retries {j.retries}
                {j.notify ? " · notify" : ""}
              </span>
            </span>
            <span className="row" style={{ gap: 6 }}>
              <Badge
                tone={
                  j.status === "done" ? "success" : j.status === "failed" ? "danger" : j.status === "running" ? "info" : "default"
                }
              >
                {j.status}
              </Badge>
              {j.status === "failed" || j.status === "queued" ? (
                <Button size="sm" variant="ghost" onClick={() => retry(j.id)}>
                  Retry
                </Button>
              ) : null}
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
