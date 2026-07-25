import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Button, Card } from "@/ui";
import { sessionManager } from "../managers";
import { useState } from "react";

export function SessionsPage() {
  const [sessions, setSessions] = useState(sessionManager.activeSessions());
  const history = sessionManager.loginHistory();
  const refresh = () => setSessions(sessionManager.activeSessions());
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Session Manager</h1>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => { sessionManager.logoutCurrent(); refresh(); }}>Logout current</Button>
          <Button size="sm" variant="danger" onClick={() => { sessionManager.logoutAll(); refresh(); }}>Logout all</Button>
        </div>
        <Card title="Active sessions">
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.sessionId} className="flex justify-between eds-type-small">
                <span>{s.device} · {s.browser} · {s.ipAddress} · {s.lastActivity}</span>
                <Button size="sm" variant="ghost" onClick={() => { sessionManager.revoke(s.sessionId); refresh(); }}>Revoke</Button>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Login history">
          <ul className="space-y-1 eds-type-small">
            {history.map((h) => (
              <li key={h.id}>{h.at} · {h.ipAddress} · {h.method} · {h.success ? "ok" : "failed"}</li>
            ))}
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
}
