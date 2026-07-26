import { Link, useParams } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { moduleRegistry } from "../managers/moduleRegistry";
import { PermissionGuard } from "@/shell/PermissionGuard";

export function WorkspaceModulePage() {
  const { module = "crm", sub } = useParams<{ module: string; sub?: string }>();
  const meta = moduleRegistry.resolve(module);
  const requires = meta.permissions?.length ? meta.permissions : ["read"];

  return (
    <PermissionGuard require={requires}>
      <WorkspaceLayout>
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge tone="success">Module Shell</Badge>
          <Badge>Sprint 30.4</Badge>
          <Badge>Shared Platform Shell</Badge>
          {meta.ecosystem ? <Badge>{meta.ecosystem}</Badge> : null}
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
              <li>
                Mission Control:{" "}
                <Link className="underline" to="/platform-builder/mission-control">
                  /platform-builder/mission-control
                </Link>
              </li>
            </ul>
          </Card>
          <Card title="Pilot readiness">
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              Connected through the shared application shell. Live workflow binding is the next
              sprint — this surface validates routing, permissions, and composition for controlled
              pilots.
            </p>
          </Card>
        </div>
      </WorkspaceLayout>
    </PermissionGuard>
  );
}
