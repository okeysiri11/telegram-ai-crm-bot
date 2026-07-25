import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card, Badge, Button } from "@/ui";
import { Link } from "react-router-dom";
import { buildAuthenticationDashboard } from "../dashboard/authDashboard";
import { sessionManager } from "../managers";

export function IdentityCenterPage() {
  const dash = buildAuthenticationDashboard();
  return (
    <DashboardLayout>
      <div className="space-y-6 eds-anim-fade">
        <div>
          <h1 className="eds-type-h1">Identity Center</h1>
          <p className="eds-type-small text-[var(--eds-text-muted)]">Authentication dashboard · users, orgs, roles, MFA, security</p>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="User overview">
            <p className="eds-type-h3">{dash.userOverview.active} / {dash.userOverview.total}</p>
            <p className="eds-type-caption">Active users</p>
          </Card>
          <Card title="Security status">
            <Badge>{dash.securityStatus.mfaStatus}</Badge>
            <p className="mt-2 eds-type-small">Risk score: {dash.securityStatus.riskScore}</p>
            <p className="eds-type-small">Failed attempts: {dash.securityStatus.failedAttempts}</p>
          </Card>
          <Card title="MFA adoption">
            <p className="eds-type-small">Methods: {dash.mfaAdoption.methods.join(", ")}</p>
            <p className="eds-type-caption mt-1">Extensions: {dash.mfaAdoption.extensionsReady.join(", ")}</p>
            <p className="eds-type-small mt-2">Backup codes left: {dash.mfaAdoption.backupCodesRemaining}</p>
          </Card>
          <Card title="Login analytics">
            <p className="eds-type-h3">{Math.round(dash.loginAnalytics.successRate * 100)}%</p>
            <p className="eds-type-caption">{dash.loginAnalytics.total} recent attempts</p>
          </Card>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Active sessions">
            <ul className="space-y-2">
              {dash.activeSessions.map((s) => (
                <li key={s.sessionId} className="flex items-center justify-between eds-type-small">
                  <span>{s.device} · {s.browser} · {s.ipAddress}</span>
                  {!s.current ? (
                    <Button size="sm" variant="ghost" onClick={() => sessionManager.revoke(s.sessionId)}>Revoke</Button>
                  ) : (
                    <Badge>current</Badge>
                  )}
                </li>
              ))}
            </ul>
            <div className="mt-3 flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => sessionManager.logoutAll()}>Logout all</Button>
              <Link className="eds-type-small text-[var(--eds-primary)]" to="/identity/sessions">Manage sessions</Link>
            </div>
          </Card>
          <Card title="Organizations">
            <ul className="space-y-1 eds-type-small">
              {dash.organizations.slice(0, 5).map((o) => (
                <li key={o.organizationId}>{o.name} · {o.kind} · {o.activeUsers} users</li>
              ))}
            </ul>
            <Link className="mt-2 inline-block eds-type-small text-[var(--eds-primary)]" to="/identity/organizations">View all</Link>
          </Card>
          <Card title="Roles & permissions">
            <p className="eds-type-small">{dash.roles.length} roles · {dash.permissionCount} permissions</p>
            <p className="eds-type-caption mt-1">{dash.permissions.join(" · ")}</p>
            <div className="mt-2 flex gap-3">
              <Link className="eds-type-small text-[var(--eds-primary)]" to="/identity/roles">Roles</Link>
              <Link className="eds-type-small text-[var(--eds-primary)]" to="/identity/permissions">Permissions</Link>
            </div>
          </Card>
          <Card title="Recent activity">
            <ul className="space-y-1 eds-type-small">
              {dash.recentActivity.map((a) => (
                <li key={a.id}>{a.kind}: {a.summary}</li>
              ))}
            </ul>
            <Link className="mt-2 inline-block eds-type-small text-[var(--eds-primary)]" to="/identity/activity">Activity center</Link>
          </Card>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link to="/identity/users"><Button size="sm">Users</Button></Link>
          <Link to="/identity/security"><Button size="sm" variant="secondary">Security</Button></Link>
          <Link to="/identity/profile"><Button size="sm" variant="secondary">Profile</Button></Link>
          <Link to="/identity/mfa"><Button size="sm" variant="secondary">MFA</Button></Link>
          <Link to="/auth/change-password"><Button size="sm" variant="ghost">Change password</Button></Link>
        </div>
      </div>
    </DashboardLayout>
  );
}
