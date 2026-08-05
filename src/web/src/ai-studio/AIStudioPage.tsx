/**
 * Enterprise AI Studio — Sprint 28.3.
 * Thin composition over Production Center + Runtime Engine.
 * No second store / job engine / design system.
 */

import { lazy, Suspense, useEffect, useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useIntegrationRuntimeHealth, useSharedContext, enterpriseEventBus } from "@/integration-hub";
import { EnterpriseRuntimeMonitor } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { webConfig } from "@/config/webConfig";
import { ProductionProviderStrip } from "@/enterprise-integrations";
import {
  AI_STUDIO_VERSION,
  studioById,
  type ProductionStudioId,
} from "@/ai-production-studio/productionCatalog";
import { useProductionStore, type ProductionView } from "@/ai-production-studio/productionStore";

const StudioWorkspace = lazy(() =>
  import("@/ai-production-studio/StudioWorkspace").then((m) => ({ default: m.StudioWorkspace })),
);
const PromptStudioPanel = lazy(() =>
  import("@/ai-production-studio/PromptStudioPanel").then((m) => ({ default: m.PromptStudioPanel })),
);
const LibraryBrowser = lazy(() =>
  import("@/ai-production-studio/LibraryBrowser").then((m) => ({ default: m.LibraryBrowser })),
);
const ProjectExplorer = lazy(() =>
  import("@/ai-production-studio/ProjectExplorer").then((m) => ({ default: m.ProjectExplorer })),
);
const GenerationHistoryPanel = lazy(() =>
  import("@/ai-production-studio/GenerationHistoryPanel").then((m) => ({
    default: m.GenerationHistoryPanel,
  })),
);
const ProductionRuntimePanel = lazy(() =>
  import("@/enterprise-runtime/ProductionRuntimePanel").then((m) => ({
    default: m.ProductionRuntimePanel,
  })),
);

const NAV: { id: ProductionView | "home"; label: string }[] = [
  { id: "home", label: "Студии" },
  { id: "projects", label: "Проекты" },
  { id: "prompts", label: "Промпты" },
  { id: "templates", label: "Шаблоны" },
  { id: "assets", label: "Ассеты" },
  { id: "media", label: "Медиа" },
  { id: "history", label: "История" },
  { id: "favorites", label: "Избранное" },
  { id: "gallery", label: "Галерея" },
  { id: "runtime", label: "Runtime" },
];

export function AIStudioPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const hydrate = useProductionStore((s) => s.hydrate);
  const hydrated = useProductionStore((s) => s.hydrated);
  const view = useProductionStore((s) => s.view);
  const setView = useProductionStore((s) => s.setView);
  const openStudio = useProductionStore((s) => s.openStudio);
  const recent = useProductionStore((s) => s.recentProjects);
  const items = useNotificationStore((s) => s.items);
  const unread = useMemo(() => items.filter((i) => !i.read).length, [items]);
  const { items: health } = useIntegrationRuntimeHealth();
  const ctx = useSharedContext();
  const aiOk = health.find((h) => h.id === "ai")?.tone !== "err";

  useEffect(() => {
    hydrate();
    document.title = "Enterprise AI Studio · ADOS";
    enterpriseEventBus.openModule("/ai-studio", "other");
  }, [hydrate]);

  const studioParam = params.get("studio");
  const tabParam = params.get("tab");
  useEffect(() => {
    const studio = studioParam as ProductionStudioId | null;
    if (studio && studioById(studio)) openStudio(studio);
    const tab = tabParam as ProductionView | null;
    if (tab && NAV.some((n) => n.id === tab)) setView(tab);
  }, [studioParam, tabParam, openStudio, setView]);

  if (!hydrated) {
    return (
      <WorkspaceLayout>
        <div className="p-6 space-y-3" data-testid="ai-studio-skeleton">
          <div className="edm-skeleton h-8 w-64 rounded-md" />
          <div className="edm-skeleton h-24 w-full rounded-lg" />
          <p className="eds-type-helper">Загрузка AI Studio…</p>
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
                Enterprise AI Studio · {AI_STUDIO_VERSION}
              </p>
              <h1 className="text-2xl font-semibold tracking-tight">Создание и управление AI-контентом</h1>
              <p className="eds-type-helper mt-1 max-w-2xl">
                Изображения · Видео · Аудио · Голос · Аватар · Промпты — на Enterprise Runtime и Production Center.
                Конвейер · редактор промптов · очередь генерации · история · провайдер · оценка стоимости.
              </p>
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <Badge tone={aiOk ? "success" : "warning"}>AI {aiOk ? "live" : "проверка"}</Badge>
              {unread ? <Badge tone="warning">Алерты {unread}</Badge> : null}
              <Badge>{ctx.organization}</Badge>
              <Link to="/production-studio">
                <Button size="sm" variant="secondary">
                  Production Center
                </Button>
              </Link>
              <Link to="/enterprise-city">
                <Button size="sm" variant="ghost">
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
          <nav className="row mt-3" style={{ gap: 6, flexWrap: "wrap" }} aria-label="Разделы AI Studio">
            {NAV.map((n) => (
              <Button
                key={n.id}
                size="sm"
                variant={view === n.id || (view === "studio" && n.id === "home") ? "primary" : "ghost"}
                toolbar
                onClick={() => setView(n.id === "home" ? "home" : n.id)}
              >
                {n.label}
              </Button>
            ))}
          </nav>
          {recent().length ? (
            <p className="eds-type-helper mt-2">
              Недавние: {recent()
                .slice(0, 4)
                .map((p) => p.title)
                .join(" · ")}
            </p>
          ) : null}
        </header>

        <Suspense
          fallback={
            <div className="space-y-2 p-4">
              <div className="edm-skeleton h-40 w-full rounded-lg" />
              <p className="eds-type-helper">Загрузка поверхности студии…</p>
            </div>
          }
        >
          {view === "home" || view === "studio" ? <StudioWorkspace coreOnly /> : null}
          {view === "projects" ? <ProjectExplorer /> : null}
          {view === "prompts" ? <PromptStudioPanel /> : null}
          {view === "templates" ? <LibraryBrowser mode="templates" /> : null}
          {view === "assets" ? <LibraryBrowser mode="assets" /> : null}
          {view === "media" || view === "gallery" ? <LibraryBrowser mode="media" /> : null}
          {view === "history" || view === "favorites" ? <GenerationHistoryPanel /> : null}
          {view === "runtime" ? <ProductionRuntimePanel /> : null}
        </Suspense>

        <Card title="Ссылки платформы">
          <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
            <Button size="sm" variant="secondary" onClick={() => navigate("/production-studio?tab=runtime")}>
              Production Runtime
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/builder-studio")}>
              AI Builder (агенты)
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/platform-builder/concierge")}>
              Concierge
            </Button>
            <Button size="sm" variant="ghost" onClick={() => navigate("/platform-builder/assets")}>
              Реестр ассетов
            </Button>
          </div>
          <p className="eds-type-helper mt-2">
            Композиция Production Center · Runtime Engine · Job Manager — без дублирования сервисов.
          </p>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
