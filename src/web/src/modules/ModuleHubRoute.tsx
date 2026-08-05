import { Navigate, useParams } from "react-router-dom";
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

export function ModulePageById({ id }: { id: string }) {
  const mod = getModuleBySlug(id);
  if (!mod) return <Navigate to="/dashboard" replace />;

  if (id === "crm") return <CrmModulePage />;
  if (id === "projects") return <ProjectsModulePage />;
  if (id === "knowledge") return <KnowledgeModulePage />;
  if (id === "documents") return <DriveModulePage />;
  if (id === "marketplace") return <MarketplaceModulePage />;
  if (id === "ai_studio") return <AiStudioModulePage />;

  return <EnterpriseModulePage module={mod} />;
}
