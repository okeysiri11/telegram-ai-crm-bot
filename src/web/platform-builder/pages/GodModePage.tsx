import { Navigate } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { GOD_CAPABILITIES } from "../managers/godMode";
import { useIsPlatformOwner } from "../managers/platformOwner";

export function GodModePage() {
  const owner = useIsPlatformOwner();
  if (!owner) {
    return <Navigate to="/platform-builder" replace />;
  }

  return (
    <PlatformBuilderLayout
      title="God Mode"
      subtitle="Isolated Platform Owner management area."
    >
      <div className="eds-grid eds-grid--dashboard">
        <Card title="Access">
          <Badge tone="success">Platform Owner</Badge>
          <p className="mt-2 eds-type-small">Hidden from every other role.</p>
        </Card>
        <Card title="System diagnostics">
          <ul className="space-y-1 eds-type-small">
            <li>Builders online</li>
            <li>Academy online</li>
            <li>Framework online</li>
            <li>API online</li>
          </ul>
        </Card>
        <Card title="Architecture">
          <p className="eds-type-small">application: platform_builder</p>
          <p className="eds-type-small">api: /api/platform-builder/v1</p>
          <p className="eds-type-small">web: src/web/platform-builder</p>
        </Card>
        <Card title="Developer console">
          <pre className="rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
            platform-builder&gt; ready
          </pre>
        </Card>
        <Card title="Version history">
          <p className="eds-type-small">Seed checkpoint · Platform Builder Core</p>
        </Card>
        <Card title="Rollback manager">
          <p className="eds-type-small">Checkpoints ready for Platform Owner rollback.</p>
        </Card>
      </div>

      <Card title="Capabilities">
        <ul className="grid gap-2 md:grid-cols-2">
          {GOD_CAPABILITIES.map((c) => (
            <li
              key={c}
              className="rounded-md border border-[var(--eds-border)] p-2 eds-type-small"
            >
              {c.replaceAll("_", " ")}
            </li>
          ))}
        </ul>
      </Card>
    </PlatformBuilderLayout>
  );
}
