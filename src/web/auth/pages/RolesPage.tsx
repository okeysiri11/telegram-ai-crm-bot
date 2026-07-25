import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card, Badge } from "@/ui";
import { roleManager } from "../managers";

export function RolesPage() {
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Role Manager</h1>
        <p className="eds-type-small text-[var(--eds-text-muted)]">Templates: {roleManager.templates().join(", ")}</p>
        <div className="eds-grid eds-grid--dashboard">
          {roleManager.list().map((r) => (
            <Card key={r.roleId} title={r.name}>
              <Badge>{r.scope}</Badge>
              <p className="mt-2 eds-type-caption">Inherits: {r.inheritsFrom.join(", ") || "—"}</p>
              <p className="eds-type-caption">Groups: {r.permissionGroups.join(", ")}</p>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
