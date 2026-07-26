import { Link, useParams } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";

type ModuleMeta = {
  title: string;
  purpose: string;
  builderRoute?: string;
  portalHint?: string;
  apiHint?: string;
};

const MODULES: Record<string, ModuleMeta> = {
  crm: {
    title: "CRM",
    purpose: "Universal CRM module shell — extends Platform Builder CRM frame and vertical CRM APIs.",
    builderRoute: "/platform-builder/crm",
    portalHint: "/portals/employee",
    apiHint: "Vertical CRM APIs (e.g. dealer CRM) + legacy /api/v1",
  },
  erp: {
    title: "ERP",
    purpose: "Universal ERP module shell — compose inventory/ops without duplicating automotive ERP.",
    builderRoute: "/platform-builder/erp",
    portalHint: "/portals/employee",
  },
  finance: {
    title: "Finance",
    purpose: "Finance module shell — binds to finance_enterprise APIs in later sprints.",
    apiHint: "/api/finance-enterprise/v1",
  },
  analytics: {
    title: "Analytics",
    purpose: "Analytics module shell — reuses Visual Intelligence and hub analytics.",
    builderRoute: "/platform-builder/intelligence",
    portalHint: "/portals/owner",
  },
  marketplace: {
    title: "Marketplace",
    purpose: "Marketplace module shell — Platform Builder marketplace frame + marketplace app API.",
    builderRoute: "/platform-builder/marketplace",
    apiHint: "/api/marketplace/v1",
  },
  ai: {
    title: "AI Workspace",
    purpose: "AI module shell — Concierge, Team, and AI OS remain platform layers.",
    builderRoute: "/platform-builder/ai-team",
    portalHint: "/ai-os",
  },
  auto: {
    title: "Automotive",
    purpose: "Automotive industry module shell — prepares Customer/Dealer portals for auto APIs.",
    builderRoute: "/platform-builder/business-ecosystem",
    portalHint: "/portals/customer",
    apiHint: "/api/auto/v1",
  },
  agro: {
    title: "Agriculture",
    purpose: "Agriculture industry module shell — grain/trade/port capabilities via agro APIs.",
    builderRoute: "/platform-builder/business-ecosystem",
    apiHint: "/api/agro/v1 · /api/agro-enterprise/v1",
  },
  beauty: {
    title: "Beauty",
    purpose: "Beauty industry module shell — extends platform_beauty libraries + hub BOS.",
    builderRoute: "/platform-builder/business-ecosystem",
  },
  hr: {
    title: "HR",
    purpose: "HR directory shell — placeholder until HR universal module binds live data.",
  },
  docs: {
    title: "Documents / Knowledge",
    purpose: "Documents shell — Knowledge Builder frame + knowledge graph extensions.",
    builderRoute: "/platform-builder/knowledge",
  },
  reports: {
    title: "Reports",
    purpose: "Reports shell — compose analytics and executive timeline views.",
    portalHint: "/portals/owner",
  },
  workflows: {
    title: "Workflows",
    purpose: "Workflows shell — Workflow Studio + Workflow Intelligence (analysis-only in PB).",
    builderRoute: "/platform-builder/workflow-intelligence",
  },
};

export function WorkspaceModulePage() {
  const { module = "crm", sub } = useParams<{ module: string; sub?: string }>();
  const meta = MODULES[module] || {
    title: module,
    purpose: "Workspace module shell — Sprint 30.3 web preparation.",
  };

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Module Shell</Badge>
        <Badge>Sprint 30.3</Badge>
        <Badge>No parallel implementation</Badge>
        {sub ? <Badge>{sub}</Badge> : null}
      </div>
      <h1 className="eds-type-title text-[var(--eds-text)]">{meta.title}</h1>
      <p className="mt-2 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">{meta.purpose}</p>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Composition">
          <ul className="eds-type-small space-y-2">
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
                Portal:{" "}
                <Link className="underline" to={meta.portalHint}>
                  {meta.portalHint}
                </Link>
              </li>
            ) : null}
            {meta.apiHint ? <li>API: {meta.apiHint}</li> : null}
            <li>
              Ecosystems:{" "}
              <Link className="underline" to="/platform-builder/business-ecosystem">
                /platform-builder/business-ecosystem
              </Link>
            </li>
          </ul>
        </Card>
        <Card title="Readiness">
          <p className="eds-type-small text-[var(--eds-text-muted)]">
            Soft-route reconciled. Live data binding and identity bridge ship in the next Web
            implementation sprint — this shell only prepares navigation and composition.
          </p>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
