import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card, Badge } from "@/ui";
import { permissionManager } from "../managers";

export function PermissionsPage() {
  const sync = permissionManager.syncWithCoreRbac();
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Permission Manager</h1>
        <p className="eds-type-small">Synced with Enterprise Core RBAC · {sync.count} permissions · {sync.source}</p>
        <div className="eds-grid eds-grid--dashboard">
          {permissionManager.domains().map((domain) => (
            <Card key={domain} title={domain}>
              <ul className="space-y-1">
                {permissionManager.byDomain(domain).map((p) => (
                  <li key={p.permissionId} className="flex items-center gap-2 eds-type-small">
                    <span>{p.action}</span>
                    {p.syncedWithRbac ? <Badge>RBAC</Badge> : null}
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
