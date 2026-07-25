import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { BUILDER_CATALOG } from "../managers/builderRegistry";
import { useIsPlatformOwner } from "../managers/platformOwner";

export function PlatformBuilderDashboard() {
  const owner = useIsPlatformOwner();
  const builders = BUILDER_CATALOG.filter(
    (b) => b.kind === "builder" || b.kind === "academy" || (b.kind === "god_mode" && owner),
  );

  return (
    <PlatformBuilderLayout
      title="Platform Builder"
      subtitle="Visual operating system for building every future object on the platform."
    >
      <div className="eds-grid eds-grid--dashboard">
        <Card title="Builder Framework">
          <p className="eds-type-small">
            Step → Explanation → Information → Example → Preview → Create
          </p>
          <Badge>Operational</Badge>
        </Card>
        <Card title="Builder Academy">
          <p className="eds-type-small">Quick Start · Guided Learning · Expert Mode</p>
          <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/academy">
            Open Academy
          </Link>
        </Card>
        <Card title="Platform Owner">
          <p className="eds-type-small">
            {owner
              ? "God Mode available for your Platform Owner role."
              : "God Mode is reserved for Platform Owner."}
          </p>
        </Card>
        <Card title="Theme">
          <p className="eds-type-small">Enterprise Design System · Dark Mode ready via theme toggle.</p>
        </Card>
      </div>

      <Card title="Builders">
        <ul className="grid gap-2 md:grid-cols-2">
          {builders.map((b) => (
            <li key={b.id}>
              <Link
                to={b.route}
                className="flex items-center justify-between rounded-md border border-[var(--eds-border)] p-3 eds-type-small transition hover:border-[var(--eds-primary)]"
              >
                <span>{b.name}</span>
                <Badge>{b.status}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </PlatformBuilderLayout>
  );
}
