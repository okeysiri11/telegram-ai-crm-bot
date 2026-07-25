import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card, Badge } from "@/ui";
import { securityCenter } from "../managers";

export function SecurityCenterPage() {
  const snap = securityCenter.snapshot();
  const events = securityCenter.events();
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Security Center</h1>
        <div className="eds-grid eds-grid--dashboard">
          <Card title="MFA status"><Badge>{snap.mfaStatus}</Badge></Card>
          <Card title="Trusted devices"><p className="eds-type-h3">{snap.trustedDevices}</p></Card>
          <Card title="Recent logins"><p className="eds-type-h3">{snap.recentLogins}</p></Card>
          <Card title="Failed attempts"><p className="eds-type-h3">{snap.failedAttempts}</p></Card>
          <Card title="Security events"><p className="eds-type-h3">{snap.securityEvents}</p></Card>
          <Card title="Password age"><p className="eds-type-h3">{snap.passwordAgeDays}d</p></Card>
          <Card title="Risk score"><p className="eds-type-h3">{snap.riskScore}</p></Card>
        </div>
        <Card title="Recent security events">
          <ul className="space-y-1 eds-type-small">
            {events.map((e) => <li key={e.id}>{e.type} · {e.at}</li>)}
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
}
