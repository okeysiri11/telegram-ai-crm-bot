import { Navigate, useParams, useSearchParams } from "react-router-dom";
import { getModuleBySlug } from "./moduleCatalog";
import { EnterpriseModulePage } from "./EnterpriseModulePage";
import { EmptyState } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import {
  CrmModulePage,
  ProjectsModulePage,
  KnowledgeModulePage,
  DriveModulePage,
  MarketplaceModulePage,
  AiStudioModulePage,
} from "@/enterprise-business";
import { MODULE_LANDINGS } from "./moduleLandingCatalog";
import { ModuleLandingView } from "./ModuleLandingView";

/** Resolves /:slug hub pages from the enterprise module catalog. */
export function ModuleHubRoute() {
  const { moduleSlug = "" } = useParams<{ moduleSlug: string }>();
  const mod = getModuleBySlug(moduleSlug);
  if (!mod) {
    return (
      <WorkspaceLayout>
        <EmptyState
          title="Модуль не найден"
          description={`Нет модуля «${moduleSlug}».`}
          actionLabel="Главная"
          actionTo="/dashboard"
          illustration="?"
        />
      </WorkspaceLayout>
    );
  }
  if (mod.id === "dashboard") return <Navigate to="/dashboard" replace />;
  if (mod.id === "settings") return <Navigate to="/settings" replace />;
  return <ModulePageById id={mod.id} />;
}

function landingIdForModule(id: string): string | undefined {
  if (id === "ai_studio") return "ai";
  if (MODULE_LANDINGS.some((m) => m.id === id)) return id;
  return undefined;
}

export function ModulePageById({ id }: { id: string }) {
  const mod = getModuleBySlug(id);
  if (!mod) return <Navigate to="/dashboard" replace />;

  const [params] = useSearchParams();
  const deep = Boolean(params.get("view") || params.get("action") || params.get("demo") === "1");
  const lid = landingIdForModule(id);
  const landing = lid ? MODULE_LANDINGS.find((m) => m.id === lid) : undefined;

  if (landing && !deep) {
    return (
      <WorkspaceLayout>
        <ModuleLandingView landing={landing} />
      </WorkspaceLayout>
    );
  }

  if (id === "crm") return <CrmModulePage />;
  if (id === "projects") return <ProjectsModulePage />;
  if (id === "knowledge") return <KnowledgeModulePage />;
  if (id === "documents") return <DriveModulePage />;
  if (id === "marketplace") return <MarketplaceModulePage />;
  if (id === "ai_studio") return <AiStudioModulePage />;

  return <EnterpriseModulePage module={mod} />;
}
