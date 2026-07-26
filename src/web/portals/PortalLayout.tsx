import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";

export function PortalLayout({
  title,
  subtitle,
  audience,
  children,
}: {
  title: string;
  subtitle: string;
  audience: "customer" | "employee" | "owner";
  children?: ReactNode;
}) {
  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Portal Shell</Badge>
        <Badge>Sprint 30.5</Badge>
        <Badge>{audience}</Badge>
        <Badge>Extends Workspace · EDS</Badge>
      </div>
      <h1 className="eds-type-title text-[var(--eds-text)]">{title}</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">{subtitle}</p>
      <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
        Composes existing platform modules — does not replace Mission Control, CRM APIs, or Builder
        Studio.{" "}
        <Link className="underline" to="/platform-builder/business-ecosystem">
          Business Ecosystem Foundation
        </Link>
      </p>
      <div className="mt-6 space-y-4">{children}</div>
    </WorkspaceLayout>
  );
}

export function PortalLinksCard({
  title,
  links,
}: {
  title: string;
  links: { label: string; to: string }[];
}) {
  return (
    <Card title={title}>
      <ul className="eds-type-small space-y-2">
        {links.map((l) => (
          <li key={l.to}>
            <Link className="underline" to={l.to}>
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
