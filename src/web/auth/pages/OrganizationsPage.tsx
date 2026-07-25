import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card } from "@/ui";
import { organizationManager } from "../managers";

export function OrganizationsPage() {
  const orgs = organizationManager.list();
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Organization Manager</h1>
        <p className="eds-type-small text-[var(--eds-text-muted)]">Companies · Departments · Teams · Branches · Projects</p>
        <div className="eds-grid eds-grid--dashboard">
          {orgs.map((o) => (
            <Card key={o.organizationId} title={o.name}>
              <p className="eds-type-small">{o.kind}</p>
              <p className="eds-type-caption">ID: {o.organizationId}</p>
              <p className="eds-type-caption">Parent: {o.parentOrganization || "—"}</p>
              <p className="eds-type-caption">Owner: {o.owner}</p>
              <p className="eds-type-caption">Users: {o.activeUsers} · License: {o.license} · {o.status}</p>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
