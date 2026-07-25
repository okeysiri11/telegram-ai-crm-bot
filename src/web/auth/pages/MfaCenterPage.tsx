import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { mfaCenter } from "../managers";
import { Link } from "react-router-dom";

export function MfaCenterPage() {
  const recovery = mfaCenter.recoveryFlow();
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">MFA Center</h1>
        <div className="eds-grid eds-grid--dashboard">
          <Card title="Enabled methods">
            <ul className="space-y-1">
              {mfaCenter.methods.map((m) => <li key={m}><Badge>{m}</Badge></li>)}
            </ul>
          </Card>
          <Card title="Extension-ready">
            <ul className="space-y-1">
              {mfaCenter.extensionsReady.map((m) => <li key={m} className="eds-type-small">{m}</li>)}
            </ul>
          </Card>
          <Card title="Status">
            <p className="eds-type-small">TOTP: {mfaCenter.status.totpEnabled ? "on" : "off"}</p>
            <p className="eds-type-small">Email code: {mfaCenter.status.emailCodeEnabled ? "on" : "off"}</p>
            <p className="eds-type-small">Backup codes: {mfaCenter.status.backupCodesRemaining}</p>
          </Card>
          <Card title="Recovery flow">
            <p className="eds-type-small">{recovery.steps.join(" → ")}</p>
            <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/auth/mfa">Challenge UI</Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
