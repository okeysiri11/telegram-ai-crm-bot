import { Link, useParams } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { moduleRegistry } from "../managers/moduleRegistry";
import { PermissionGuard } from "@/shell/PermissionGuard";
import { WORKSPACE_MODULE_ROUTES } from "@/enterprise-workspace";

const HUB_BY_MODULE: Record<string, string> = {
  crm: "/crm",
  erp: "/erp",
  docs: "/documents",
  documents: "/documents",
  marketplace: "/marketplace",
  finance: "/workspace/finance",
  legal: "/workspace/legal",
  knowledge: "/knowledge",
  analytics: "/analytics",
  projects: "/projects",
  ai: "/ai-agents",
};

/**
 * Sprint 30.7 — Workspace module shell with real module links (no empty placeholders).
 */
export function WorkspaceModulePage() {
  const { module = "crm", sub } = useParams<{ module: string; sub?: string }>();
  const meta = moduleRegistry.resolve(module);
  const requires = meta.permissions?.length ? meta.permissions : ["read"];
  const hub = HUB_BY_MODULE[module] || meta.portalHint || `/workspace/${module}`;

  return (
    <PermissionGuard require={requires}>
      <WorkspaceLayout>
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge tone="success">Модуль</Badge>
          <Badge>Sprint 30.7</Badge>
          <Badge>Enterprise Workspace</Badge>
          {meta.ecosystem ? <Badge>{meta.ecosystem}</Badge> : null}
          {sub ? <Badge>{sub}</Badge> : null}
        </div>
        <h1 className="eds-type-title text-[var(--eds-text)]">{meta.title}</h1>
        <p className="mt-2 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">{meta.purpose}</p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Link to={hub}>
            <Button>Открыть рабочую поверхность</Button>
          </Link>
          {meta.builderRoute ? (
            <Link to={meta.builderRoute}>
              <Button variant="secondary">Конструктор</Button>
            </Link>
          ) : null}
          <Link to="/search">
            <Button variant="ghost">Глобальный поиск</Button>
          </Link>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card title="Связи платформы">
            <ul className="eds-type-small space-y-2">
              <li>
                Хаб:{" "}
                <Link className="underline" to={hub}>
                  {hub}
                </Link>
              </li>
              {meta.builderRoute ? (
                <li>
                  Builder:{" "}
                  <Link className="underline" to={meta.builderRoute}>
                    {meta.builderRoute}
                  </Link>
                </li>
              ) : null}
              {meta.portalHint ? (
                <li>
                  Портал:{" "}
                  <Link className="underline" to={meta.portalHint}>
                    {meta.portalHint}
                  </Link>
                </li>
              ) : null}
              {meta.apiHint ? <li>API: {meta.apiHint}</li> : null}
              <li>
                Город:{" "}
                <Link className="underline" to="/city">
                  /city
                </Link>
              </li>
              <li>
                Здоровье:{" "}
                <Link className="underline" to="/health">
                  /health
                </Link>
              </li>
            </ul>
          </Card>
          <Card title="Модули workspace">
            <ul className="eds-type-small space-y-2">
              {WORKSPACE_MODULE_ROUTES.map((r) => (
                <li key={r.id}>
                  <Link className="underline" to={r.route}>
                    {r.label}
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </WorkspaceLayout>
    </PermissionGuard>
  );
}
